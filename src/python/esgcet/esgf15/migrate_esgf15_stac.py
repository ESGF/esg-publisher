from pandas.compat.pyarrow import pa_version_under14p0
from pydantic import validate_call
from typing import Literal
from pathlib import Path
import yaml
from platformdirs import PlatformDirs
from typing import Any

from esgcet.esgf15.globus import ESGFGlobusIndex, Project
from esgcet.stac_converter import ESGSTACConverter
from esgcet.stac_client import getTransactionClient
import esgcet.logger as logger

log = logger.ESGPubLogger()
publog = log.return_logger(__name__)

DATA_NODE_MAPPING={
    "anl": "eagle.alcf.anl.gov",
    "ornl": "esgf-node.ornl.gov",
    "nersc": "esgf-data.nersc.gov"
}

@validate_call
def migrate(*,
    institution_id: str,
    data_node: Literal["anl", "ornl", "nersc"],
    project: Project,
    dataset_limit: int = 1000,
    config_file: Path | None,
    total: int | None = None,
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

    esgf15_index = ESGFGlobusIndex()

    esgf15_generator = esgf15_index.query_dataset_file(
        project = project,
        fixed_facet = {"institution_id": institution_id},
        data_node = DATA_NODE_MAPPING[data_node],
        is_replica = True,
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
        stac_data = []
        for entry in record:
            dataset_id = entry[0].get("id")
            type_fixed_docs = _esgf1_5_type_conversion(entry)
            if type_fixed_docs is None:
                publog.error(f"{dataset_id} error in type fixes")
                continue

            stac_item = esgf_stac_convert.convert2stac(type_fixed_docs)
            if stac_item is None:
                publog.error(f"{dataset_id} cannot be converted to stac")
                continue

            stac_data.append(stac_item)

            try:
                rc = tc.publish(stac_item)
                if total and no_published >= total:
                    return
                no_published += 1

            except Exception as ex:
                 publog.error(f"some error happened during stac publishing: {ex}")


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
