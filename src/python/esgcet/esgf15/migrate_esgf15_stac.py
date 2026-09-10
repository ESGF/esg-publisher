from pandas.compat.pyarrow import pa_version_under14p0
from pydantic import validate_call, ConfigDict
from typing import Literal
from pathlib import Path
import yaml
from platformdirs import PlatformDirs
from typing import Any

from esgcet.esgf15.globus import ESGFGlobusIndex, Project
from esgcet.stac.stac_converter import ESGSTACConverter, ESGSTACItem
from esgcet.stac.stac_client import getTransactionClient

from esgcet.util import logger
from esgcet.kerchunk.kerchunk_generator import KerchunkGenerator

import duckdb
from duckdb import DuckDBPyConnection
import json

log = logger.ESGPubLogger()
publog = log.return_logger(__name__)

DATA_NODE_MAPPING={
    "anl": "eagle.alcf.anl.gov",
    "ornl": "esgf-node.ornl.gov",
    "nersc": "esgf-data.nersc.gov"
}

NODE_LOCAL_PATH_MAPPINGS = {
    "esgf-node.ornl.gov": (
        "https://esgf-node.ornl.gov/thredds/fileServer", 
        "/nl/themis/esgf/cli137/world-shared/globus"
    )
}

@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def migrate(*,
    institution_id: str,
    data_node: Literal["anl", "ornl", "nersc"],
    project: Project,
    is_replica: bool = False,
    dataset_limit: int = 1000,
    config_file: Path | None,
    total: int | None = None,
    init_marker: str | None = None,
    method: str = "drs",
    con: DuckDBPyConnection | None = None,
) -> None:
    """migrate esgf1.5 cmip6 records to stac collections/items and
       plubish them to stac catalog"""

    if dataset_limit > 2000:
        raise ValueError(
            "suggested vaule is < 2000, if not, "
            "the next globus post search may exceed its maximum 10000!!!"
        )

    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

    else:
        platform_dirs = PlatformDirs("esg_publisher", "ESGF2-US")

        alt_config_file = Path(platform_dirs.user_config_dir) / "esg.yaml"
        if alt_config_file.exists():

            publog.info("use the config file in the system directory")
            with open(alt_config_file, 'r') as file:
                config = yaml.safe_load(file)
        else:
            raise ValueError("Please provide valid config file")

    if 'stac_config' not in config:
        raise ValueError("please provide stac_config in the config file")
    else:
        if not config.get('stac_config').get('stac_api', None):
            raise ValueError("stac_api is missing")


    esgf_stac_convert = ESGSTACConverter(config.get('stac_config'))

    esgf15_index = ESGFGlobusIndex(init_marker=init_marker)

    esgf15_generator = esgf15_index.query_dataset_file(
        project = project,
        fixed_facet = {
            "institution_id": institution_id,
            "latest": True,
            "retracted": False,
        },
        data_node = DATA_NODE_MAPPING[data_node],
        is_replica = is_replica,
        dataset_limit = dataset_limit,
    )

    TransactionClient = getTransactionClient(config.get("stac_config"))
    argdict = {
        "verbose": False,
        "dry_run": False,
        "save_stac": False,
        "silent": False,
        "stac_config": config.get('stac_config'),
    }
    tc = TransactionClient(argdict)
    if not tc:
        raise RuntimeError("Failed to create STAC transaction client")


    no_published = 1
    for record in esgf15_generator:

        for entry in record:
            error_msg = ""
            stac_submission = 0
            kc_file = ""

            dataset_id = entry[0].get("id")
            type_fixed_docs = _esgf1_5_type_conversion(entry)
            if type_fixed_docs is None:
                publog.error(f"{dataset_id} error in type fixes")
                error_msg += f"{dataset_id} error in type fixes"

                _log2db(
                    dataset_id,
                    esgf15_index.marker,
                    esgf15_index.next_marker,
                    kc_file,
                    stac_submission,
                    error_msg,
                    con,
                )

                continue

            # generate kerchunk

            try:
                publog.info("Staring the kerchunk")
                mapping = NODE_LOCAL_PATH_MAPPINGS.get(
                    DATA_NODE_MAPPING[data_node]
                )
                if mapping:
                    remote_prefix, local_prefix = mapping
                else:
                    raise ValueError("Cannot get the remote-local path mapping")

                ncfiles = _extract_local_file_paths(entry)

                local_dset_path = Path(ncfiles[0]).parent

                output_file = _get_output_file(
                    local_prefix,
                    dataset_id,
                    local_dset_path,
                    type_fixed_docs, 
                    project.value,
                    method
                )

                
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)

                if config.get("kerchunk").get("format") == "json":
                    kcfile_url = str(output_file).replace(local_prefix, remote_prefix) + '.json'
                else:
                    kcfile_url = str(output_file).replace(local_prefix, remote_prefix) + '.parq'

                generator = KerchunkGenerator(
                    path_url=ncfiles,
                    backend=config.get("kerchunk").get("backend", "kerchunk"),
                    output_file=output_file,
                    format=config.get("kerchunk").get("format", "json")
                )

                inline_threshold = config.get("kerchunk").get("inline_threshold", 0)
                generator.generate(local_prefix, remote_prefix, inline_threshold)

                # only generate successfully
                kc_file = str(output_file)

                #type_fixed_docs[0]["reference_file"] = kcfile_url


            except ValueError as e:

                error_msg += f"cannot generate kerchunk file for dataset: {dataset_id} \ndue to {e}"
                publog.error(f"cannot generate kerchunk file for dataset: {dataset_id} \ndue to {e}")

            stac_item = esgf_stac_convert.convert2stac(type_fixed_docs)
            if stac_item is None:
                error_msg += f"{dataset_id} cannot be converted to stac"
                publog.error(f"{dataset_id} cannot be converted to stac")

                _log2db(
                    dataset_id,
                    esgf15_index.marker,
                    esgf15_index.next_marker,
                    kc_file,
                    stac_submission,
                    error_msg,
                    con,
                )


                continue


            try:

                # add aggreate
                si = ESGSTACItem(stac_item)
                site = DATA_NODE_MAPPING[data_node]

                operation = si.add_aggregate("kerchunk", kcfile_url, site)

                stac_item["assets"]["reference_file"] = operation[0]["value"]
                stac_item["assets"]["reference_file"]["protocol"] = "https"

                rc = tc.publish(stac_item)

                if rc:
                    stac_submission = 1
                else:
                    error_msg += "some errors in stac publishing"

            except Exception as ex:
                 error_msg += f"some error happened during stac publishing: {ex}"
                 publog.error(f"some error happened during stac publishing: {ex}")

            # log

            _log2db(
                dataset_id,
                esgf15_index.marker,
                esgf15_index.next_marker,
                kc_file,
                stac_submission,
                error_msg,
                con,
            )

            if total and no_published >= total:
                return
            no_published += 1


def _log2db(
    dataset_id: str,
    marker: str,
    next_marker: str,
    kc_file: str,
    stac_submission: int,
    error_msg: str,
    con: DuckDBPyConnection,
) -> None:

    con.execute(
        """
        INSERT INTO log_table 
        (timestamp, dataset_id, marker, next_marker, kerchunk_file, stac_submission, message) 
        VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
        """,
        [dataset_id, marker, next_marker, kc_file, stac_submission, error_msg]
    )

def _get_output_file(
    local_prefix: str,
    dataset_id: str,
    local_dset_path: Path,
    entry: dict[str, Any],
    project_value: str,
    method: str = Literal["drs", "simple"],
) -> str | Path:

    dset_id = dataset_id.split('|')[0]

    if method == "simple":
        variable_id = entry[0].get("variable_id")
        variable_id = variable_id[0] if isinstance(variable_id, list) else variable_id
        experiment_id = entry[0].get("experiment_id")
        experiment_id = experiment_id[0] if isinstance(experiment_id, list) else experiment_id
        table_id = entry[0].get("table_id")
        table_id = table_id[0] if isinstance(table_id, list) else table_id

        local_kc_file = (
            "user_pub_work/Kerchunk/"
            f"{project_value}/{variable_id}/{experiment_id}/{table_id}/{dset_id}.kerchunk"
        )
        new_output_file = Path(local_prefix) / Path(local_kc_file)

    elif method == "drs":
        output_file = local_dset_path / Path(f"{dset_id}.kerchunk")
        parts = Path(output_file).parts
        idx = parts.index(project_value)
        new_output_file = Path(local_prefix, "user_pub_work/Kerchunk", *parts[idx:])
    
    return new_output_file


def _extract_local_file_paths(
    dataset_doc: list[dict[str, Any]],
) -> list[Path]:


    temp = dataset_doc[0].get('id').split('|')
    dataset_id = temp[0]
    data_node = temp[1] if len(temp) > 1 else None

    # https://esgf-node.ornl.gov/thredds/fileServer/user_pub_work/CMIP6Plus/LESFMIP/MOHC/HadGEM3-GC31-LL/hist-lu/f2023-r11i1p1f3/APfx/sftlf/gn/v20240102/sftlf_APfx_HadGEM3-GC31-LL_hist-lu_f2023-r11i1p1f3_gn.nc
    if "HTTPServer" in dataset_doc[0].get("access"):
        counter = 0

        mapping = NODE_LOCAL_PATH_MAPPINGS.get(data_node)

        local_paths = []
        if mapping:
            for doc in dataset_doc:
                if doc.get("type") != "File":
                    continue

                urls = doc.get("url")
                for url in urls:
                    if not url.endswith("|application/netcdf|HTTPServer"):
                        continue

                    url_split = url.split("|")
                    href = url_split[0] 
                    remote_prefix, local_prefix =  mapping
                    if href.startswith(remote_prefix):
                        local_path = href.replace(
                            remote_prefix,
                            local_prefix,
                            1,
                        )
                        local_paths.append(local_path)

    if len(local_paths) == 0:
        raise ValueError("Cannot figure out local paths of nc files")

    return local_paths




def _esgf1_5_type_conversion(
    dataset_doc: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Type fixes of ESGF 1.5 document field for STAC conversion."""

    type_fix_fields = {
        "project",
        "tracking_id",
        "pid",
        "checksum_type",
        "checksum",
        "citation_url",
    }

    type_fixed_docs = []

    for doc in dataset_doc:
        type_fixed_doc = doc.copy()

        # Convert selected fields from list -> scalar
        for field in type_fix_fields:
            value = type_fixed_doc.get(field)

            if isinstance(value, list):
                if not value:
                    publog.warning(f"Empty ESGF field: {field}")
                    return None

                type_fixed_doc[field] = value[0]
        # Convert version to string
        if "version" in type_fixed_doc and type_fixed_doc["version"] is not None:
            type_fixed_doc["version"] = str(type_fixed_doc["version"])

        type_fixed_docs.append(type_fixed_doc)

    return type_fixed_docs
