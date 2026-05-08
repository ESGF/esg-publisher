from pydantic import validate_call
from typing import Literal
from pathlib import Path
import yaml
from platformdirs import PlatformDirs
from typing import Any

from esgcet.esgf15.globus import ESGFGlobusIndex, Project
from esgcet.stac_converter import ESGSTACConverter
from esgcet.stac_client import getTransactionClient

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

            print ("use the config file in the system directory")
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
        stac_data =  [
            esgf_stac_convert.convert2stac(_esgf1_5_type_conversion(entry)) 
            for entry in record
        ]
        for stac_item in stac_data:
            try:
                rc = tc.publish(stac_item)
                if total and no_published >= total:
                    return
                no_published += 1

            except Exception as ex:
                 print (f"error: {ex}")


def _esgf1_5_type_conversion(
    dataset_doc: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Convert the esgf1.5 types for stac_converter."""
    new_dataset_doc = [] 
    for doc in dataset_doc:
        # list -> scalar
        doc["project"] = doc["project"][0] if isinstance(doc["project"], list) else doc["project"]
        if 'tracking_id' in doc:
            doc["tracking_id"] = doc["tracking_id"][0] if isinstance(doc["tracking_id"], list) else doc["tracking_id"]
        if 'checksum_type' in doc:
            doc["checksum_type"] = doc["checksum_type"][0] if isinstance(doc["checksum_type"], list) else doc["checksum_type"]
        if 'checksum' in doc:
            doc["checksum"] = doc["checksum"][0] if isinstance(doc["checksum"], list) else doc["checksum"]
        doc["citation_url"] = doc["citation_url"][0] if isinstance(doc["citation_url"], list) else doc["citation_url"] 
        # int to str
        doc["version"] = str(doc["version"]) 
        new_dataset_doc.append(doc)

    return new_dataset_doc
