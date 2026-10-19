from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from esgcet.util import logger

from esgcet.stac.stac_converter import ESGSTACConverter, ESGSTACItem
from esgcet.stac.stac_client import (
    getTransactionClient,
    GlobusTransactionClient,
    EGITransactionClient,
)
from esgcet.kerchunk.kerchunk_generator import KerchunkGenerator

import duckdb
from duckdb import DuckDBPyConnection
from esgcet.esgf15.data_node_config import (
    DATA_NODE_MAPPING,
    NODE_LOCAL_PATH_MAPPINGS
)


log = logger.ESGPubLogger()
publog = log.return_logger(__name__)

class KerchunkResult(BaseModel):
    dataset_id: str
    success: bool = False
    dset_file_docs: list[dict[str, Any]] | None = None
    kc_file: str = ""
    kc_file_url: str = ""
    marker: str | None = None
    next_marker: str | None = None
    error_msg: str = ""


# DASK WORKER FUNCTION
def generate_kerchunk_for_entry(
    entry: list[dict[str,Any]],
    dataset_id: str | None,
    config: dict[str, Any],
    project_value: str,
    drs_method: Literal["drs", "simple", "cfg"],
    type_conversion: bool=True,
) -> KerchunkResult:
    """
    Generate a Kerchunk reference for ONE ESGF dataset entry.

    This function is executed by a Dask worker.

    One entry contains one dataset doc and multiple file docs. All of those
    files are processed together and produce one Kerchunk reference file.

    Parameters
    ----------
    entry
        One ESGF 1.5 dataset entry. It may contain several file docs.

    dataset_id
        ESGF dataset_id with `|data_node` format

    config
        Publisher configuration dictionary.

    project_value
        ESGF project object.

    drs_method
        Kerchunk/output directory struncture method.

    Returns
    -------
    dict
        A small result dictionary containing the information required by
        the driver for STAC publishing and DuckDB logging.
    """

    # Get the dataset identifier before doing any expensive work.

    #dataset_id = entry[0].get("id")
    # from argument instead

    if not dataset_id or dataset_id == "<unknown>":
        return KerchunkResult(
            dataset_id="<unknown>",
            success=False,
            error_msg="Entry does not contain a dataset id",
        )


    try:
        # Fix ESGF 1.5 metadata types
        publog.info(f"Starting kerchuck generation for {dataset_id}")

        if type_conversion:
            type_fixed_docs = _esgf1_5_type_conversion(entry)
        else:
            type_fixed_docs = entry

        if type_fixed_docs is None:
            return KerchunkResult(
                dataset_id=dataset_id,
                success=False,
                error_msg=f"{dataset_id} error in type fixes",
            )

        # Determine local and remote path mapping

        #site = DATA_NODE_MAPPING[data_node]
        #mapping = NODE_LOCAL_PATH_MAPPINGS.get(site)
        site = config.get("data_node")
        data_roots = config.get("data_roots")
        mapping = get_mapping(site, data_roots)

        if not mapping:
            raise ValueError(
                f"Cannot get the remote-local path mapping for {site}"
            )

        remote_prefix, local_prefix = mapping

        # Extract all local NetCDF files for this dataset

        ncfiles = _extract_local_file_paths(type_fixed_docs, mapping)

        if not ncfiles:
            raise ValueError(
                f"No local NetCDF files found for dataset {dataset_id}"
            )

        # All NetCDF files belonging to this ESGF entry are handled by
        # this ONE Dask task.
        local_dset_path = Path(ncfiles[0]).parent

        kerchunk_config = config.get("kerchunk", None)
        if kerchunk_config is None:
            raise ValueError("not kerchunk section in config yaml")

        relative_path = kerchunk_config.get("relative_path", "./")

        relative_path = relative_path.lstrip('/')


        if drs_method == "cfg":
            xdrs_method = kerchunk_config.get("drs_method", "simple")
        else:
            xdrs_method = drs_method

        # Determine Kerchunk output file
        output_file = _get_output_file(
            local_prefix,
            dataset_id,
            local_dset_path,
            type_fixed_docs,
            project_value,
            xdrs_method,
            relative_path,
        )

        output_file = Path(output_file)

        # ``exist_ok=True`` is safe when several tasks create different
        # files under the same directory.
        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Construct the remote Kerchunk URL


        kc_format = kerchunk_config.get(
            "format",
            "json",
        )

        kc_backend = kerchunk_config.get(
            "backend",
            "kerchunk",
        )

        inline_threshold = kerchunk_config.get(
            "inline_threshold",
            0,
        )


        output_file_str = str(output_file)
        if not output_file_str.startswith(local_prefix):
            raise ValueError(
                f"Output file {output_file_str} is not under "
                f"local prefix {local_prefix}"
            )

        if kc_format == "json":
            kc_file_url = (
                str(output_file)
                .replace(local_prefix, remote_prefix)
                + ".json"
            )
        elif kc_format == "parquet":
            kc_file_url = (
                str(output_file)
                .replace(local_prefix, remote_prefix)
                + ".parq"
            )
        else:
            raise ValueError(
                f"Unsupported Kerchunk format: {kc_format}"
            )


        # Create and run the Kerchunk generator
        generator = KerchunkGenerator(
            path_url=ncfiles,
            backend=kc_backend,
            output_file=str(output_file),
            format=kc_format,
        )

        # This is the expensive part of the Dask task.
        # Each worker processes all NetCDF files belonging to this
        # dataset and creates one combined reference file.
        generator.generate(
            local_prefix,
            remote_prefix,
            inline_threshold,
        )

        # Return successful result to the driver
        return KerchunkResult(
            dataset_id=dataset_id,
            success=True,
            dset_file_docs=type_fixed_docs,
            kc_file=str(output_file),
            kc_file_url=kc_file_url,
        )

    except Exception as ex:
        # Catch all worker-side errors.
        return KerchunkResult(
            dataset_id=dataset_id,
            error_msg=f"{dataset_id} cannot generate kerchunk: "
                      f"{type(ex).__name__}: {ex}"
        )




def process_publish_result(
    result: KerchunkResult,
    config: dict[str, Any],
    con: DuckDBPyConnection,
    data_node: str,
    esgf_stac_convert: ESGSTACConverter,
    tc: GlobusTransactionClient | EGITransactionClient,
) -> int:
    """Convert, publish, and log a Kerchunk result.

    Returns
    -------
    int
        1 if the STAC item was successfully published, otherwise 0.
    """

    dataset_id = result.dataset_id
    error_msg = result.error_msg
    stac_submission = 0

    if not result.success:
        publog.error(f"{dataset_id}: {error_msg}")

        _log2db(
            dataset_id,
            result.marker,
            result.next_marker,
            result.kc_file,
            stac_submission,
            error_msg,
            con,
        )
        return 0

    try:
        stac_item = esgf_stac_convert.convert2stac(
            result.dset_file_docs
        )

        if stac_item is None:
            raise ValueError(
                f"{dataset_id} cannot be converted to STAC"
            )

        si = ESGSTACItem(stac_item)

        #site = DATA_NODE_MAPPING[data_node]
        site = config.get("data_node")

        operation = si.add_aggregate(
            "kerchunk",
            result.kc_file_url,
            site,
        )

        stac_item["assets"]["reference_file"] = operation[0]["value"]

        rc = tc.publish(stac_item)

        if rc:
            stac_submission = 1
        else:
            error_msg += "some errors in STAC publishing"

    except Exception as ex:
        error_msg += (
            f"some error happened during STAC publishing: {ex}"
        )
        publog.error(f"{dataset_id}: {error_msg}")

    _log2db(
        dataset_id,
        result.marker,
        result.next_marker,
        result.kc_file,
        stac_submission,
        error_msg,
        con,
    )

    return stac_submission


# some helper functions

def _get_output_file(
    local_prefix: str,
    dataset_id: str,
    local_dset_path: Path,
    entry: list[dict[str, Any]],
    project_value: str,
    method: Literal["drs", "simple"],
    relative_path: str,
) -> str | Path:

    dset_id = dataset_id.split('|')[0]

    try:
        if method == "simple":
            variable_id = entry[0].get("variable_id")
            variable_id = variable_id[0] if isinstance(variable_id, list) else variable_id
            experiment_id = entry[0].get("experiment_id")
            experiment_id = experiment_id[0] if isinstance(experiment_id, list) else experiment_id
            table_id = entry[0].get("table_id")
            table_id = table_id[0] if isinstance(table_id, list) else table_id

            local_kc_file = (
                #"user_pub_work/Kerchunk/"
                f"{relative_path}/"
                f"{project_value}/{variable_id}/{experiment_id}/{table_id}/{dset_id}.kerchunk"
            )
            new_output_file = Path(local_prefix) / Path(local_kc_file)

        elif method == "drs":
            output_file = local_dset_path / Path(f"{dset_id}.kerchunk")
            parts = Path(output_file).parts
            idx = parts.index(project_value)
            #new_output_file = Path(local_prefix, "user_pub_work/Kerchunk", *parts[idx:])
            new_output_file = Path(local_prefix, relative_path, *parts[idx:])

        else:
            raise ValueError(f"Unsupported DRS method: {method}")
    except Exception as ex:
        publog.error(f"Error in generate output file name {ex}")

    return new_output_file

def _extract_local_file_paths(
    dataset_doc: list[dict[str, Any]],
    mapping: tuple[str, str],
) -> list[Path]:

    dataset_rec = _extract_dataset_record(dataset_doc)

    temp = dataset_rec.get('id').split('|')
    dataset_id = temp[0]
    data_node = temp[1] if len(temp) > 1 else None

    # https://esgf-node.ornl.gov/thredds/fileServer/user_pub_work/CMIP6Plus/LESFMIP/MOHC/HadGEM3-GC31-LL/hist-lu/f2023-r11i1p1
    try:
        if "HTTPServer" in dataset_rec.get("access"):
            counter = 0

            #mapping = NODE_LOCAL_PATH_MAPPINGS.get(data_node)

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

    except (TypeError, ValueError) as ex:
        publog.error(f"Error in extract local file paths: {ex}")

    if len(local_paths) == 0:
        raise ValueError("Cannot figure out local paths of nc files")

    return local_paths

def _extract_dataset_record(
    dataset_doc: list[dict[str, Any]],
) -> dict[str, Any]:

    for rec in dataset_doc:
        if rec.get("type") == 'Dataset':
            return rec

    raise ValueError("cannot find dataset record in the entry")


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

        # change the http to https
        if "url" in type_fixed_doc:
             type_fixed_doc["url"] = [
                 "https://" + url[len("http://"):]
                 if url.startswith("http://")
                 else url
                 for url in type_fixed_doc["url"]
             ]

        #

        type_fixed_docs.append(type_fixed_doc)

    return type_fixed_docs


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


class ProcessLog:
    def __init__(self, csv_file:str):
        self.con: DuckDBPyConnection = duckdb.connect(database=':memory:')
        self.con.execute("""
            CREATE TABLE log_table (
                timestamp TIMESTAMP,
                dataset_id VARCHAR,
                marker VARCHAR,
                next_marker VARCHAR,
                kerchunk_file VARCHAR,
                stac_submission INTEGER,
                message VARCHAR
            )
        """)
        self.log_file = csv_file

    def log_update(
        self,
    ) -> None:
        self.con.execute(f"COPY log_table TO '{self.log_file}' (FORMAT CSV, HEADER TRUE)")


def get_mapping(
    data_node: str,
    data_roots: dict[str, str],
) -> tuple[str, str]:

    try: 
        (loc, rel), = data_roots.items()

        local_path = Path(loc)
        relative_path = Path(rel)

        assert local_path.parts[-len(relative_path.parts):] == relative_path.parts

        parent_path = local_path
        for _ in relative_path.parts:
            parent_path = parent_path.parent


        local_prefix = str(parent_path)
        remote_prefix = f"https://{data_node}/thredds/fileServer"

        return remote_prefix, local_prefix

    except Exception as ex:
        publog.error("error get the mapping, return None")
        return None
