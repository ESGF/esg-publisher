from types import MappingProxyType
from typing import Final

DATA_NODE_MAPPING: Final = MappingProxyType({
    "anl": "eagle.alcf.anl.gov",
    "ornl": "esgf-node.ornl.gov",
    "nersc": "esgf-data.nersc.gov",
})

NODE_LOCAL_PATH_MAPPINGS: Final = MappingProxyType({
    "esgf-node.ornl.gov": (
        "https://esgf-node.ornl.gov/thredds/fileServer",
        "/nl/themis/esgf/cli137/world-shared/globus",
    ),
})
