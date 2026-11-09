import re
from datetime import datetime, timezone
from esgcet.util.logger import ESGPubLogger

from esgf_core_utils.models.aggregation_assets import (
    ASSET_AGG_DESCRIPTIONS,
    ASSET_AGG_MIMETYPES,
    AGGREGATED_ASSETS
)

from esgcet.util.settings import (
    MAP_properties,
    SOURCE_properties,
    STAC_item_properties,
    STAC_list_properties,
    STAC_proj_item_properties,
<<<<<<< HEAD
    STAC_schema_versions,
=======
    STAC_schema_versions
>>>>>>> 79fafb9 (Updated for use of esgvoc for new projects)
)
from esgvoc.apps.jsg import json_schema_generator as jsg
from esgcet.util import logger


log = logger.ESGPubLogger()

log = ESGPubLogger()

class ESGSTACItem:
    """
    Container class for the item with Methods to add Assets
    """

    def __init__(self, si):
        # Store the STAC item, even if None
        # Callers should check si before creating ESGSTACItem
        self.stac_item = si
        
<<<<<<< HEAD
    def remove_aggregate(self, site):
        operations = []
        if "reference_file" in self.stac_item.get("assets", {}) and site in self.stac_item["assets"]["reference_file"].get("alternate", {}):
            path = f"/assets/reference_file/alternate/{site}"
            operations.append({
                    "op": "remove",
                    "path": path
                    })
        elif "reference_file" in self.stac_item.get("assets", {}) and self.stac_item["assets"]["reference_file"]["alternate:name"] == site:
            path = f"/assets/reference_file"
            operations.append({
                    "op": "remove",
                    "path": path
                    })
        return operations
=======
    def remove_aggregate(self, aggtypes: str | list | None = None, site: str | None = None) -> list:

        if aggtypes is None:
            aggtypes = list(ASSET_AGG_DESCRIPTIONS.keys())

        if not isinstance(aggtypes, list):
            aggtypes = [aggtypes]

        path = None

        located = False
        for aggtype in aggtypes:
            if aggtype not in self.stac_item.get("assets", {}):
                continue

            if located:
                raise ValueError(
                    'Unable to remove unspecified aggregation assets where '
                    'multiple assets are present.'
                )
            
            located = True
            if site in self.stac_item["assets"][aggtype].get("alternate", {}):
                path = f"/assets/{aggtype}/alternate/{site}"
            else:
                path = f"/assets/{aggtype}"

        if path is not None:
            return [{
                "op": "remove",
                "path": path
            }]
        return []

    def add_aggregate(self, aggtype: str, url: str, site: str) -> list:

        existing_template = self.stac_item.get('assets',{}).get(aggtype,{})

        description = ASSET_AGG_DESCRIPTIONS.get(
            aggtype,"Kerchunk reference file for virtual aggregation")

        aggmime = ASSET_AGG_MIMETYPES.get(
            aggtype,'kerchunk')


        # Sets the protocol to use for the url
        for protocol in ['https','http','s3']:
            if protocol in url:
                break

        # Override for kerchunk parquet stores
        if aggtype == 'kerchunk' and 'parq' in url:
            protocol = 'kerchunk'
>>>>>>> 79fafb9 (Updated for use of esgvoc for new projects)

    def add_aggregate(self, aggtype, url, site):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        value = {
            "href": url,
            "type": f"application/{aggtype}",
            "role": ["data", "virtual"],
            "description": "Kerchunk reference file for virtual aggregation",
            "alternate:name": site,
            "created": now,
            "updated": now,
            "protocol": "kerchunk",
        }

<<<<<<< HEAD
        if "reference_file" in self.stac_item.get("assets", {}):
            path = f"/assets/reference_file/alternate/{site}"
        else:
            path = f"/assets/reference_file"
        #    value["file:size"] =
        operations = [{
                    "op": "add",
                    "path": path,
                    "value": value
                    }]
=======
        if aggtype in self.stac_item.get("assets", {}):
            path = f"/assets/{aggtype}/alternate/{site}"
        else:
            path = f"/assets/{aggtype}"
>>>>>>> 79fafb9 (Updated for use of esgvoc for new projects)

        return operations

    def add_replica(self, rep_datanode, template, prefix, rep_globus=""):
        assets = self.stac_item.get("assets", {})
        operations = []
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")        
        for name, asset in assets.items():

            if name in AGGREGATED_ASSETS:
                continue

            if asset.get("alternate:name") == rep_datanode:
                continue

            if rep_datanode in asset.get("alternate", {}):
                continue

            replica_asset = {
                "description": asset.get("description"),
                "type": asset.get("type"),
                "roles": asset.get("roles", []),
                "alternate:name": rep_datanode,
                "created": asset.get("created"),
                "updated": now,
            }
            rep_path = "TEST/PATH"
            rep_path = asset.get("file:local_path", rep_path)

            if name == "globus":
                if not rep_globus:
                    continue
                replica_asset["href"] = (
                    f"https://app.globus.org/file-manager?"
                    f"origin_id={rep_globus}&origin_path=/{prefix}/{rep_path}"
                )

            elif asset.get("type") == "application/netcdf":
                replica_asset["href"] = template.format(prefix, rep_path)
            op = {
                "op": "add",
                "path": f"/assets/{name}/alternate/{rep_datanode}",
                "value": replica_asset,
            }
            operations.append(op)

        return operations

class ESGSTACConverter:
    def __init__(self, stac_config):
        self.stac_api = stac_config.get("stac_api", "")
        self.publog = log.return_logger("ESGSTACConverter", silent=False, verbose=False)

    def citation_link_d(self, url):

        return {"rel": "cite-as", "type": "application/json", "href": url}

    def convert2stac(self, json_data):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        dataset_doc = {}
        for doc in json_data:
            if doc.get("type") == "Dataset":
                dataset_doc = doc
                break

        assets = {}
        item_id = dataset_doc.get("instance_id")
        drspath = item_id.replace(".", "/")

        collection = dataset_doc.get("project")
        if collection == "mip-drs7":
            collection = "cmip7"

        namespace = collection.lower()

        if "Globus" in dataset_doc.get("access"):
            for doc in json_data:
                if doc.get("type") == "File":
                    urls = doc.get("url")
                    for url in urls:
                        if url.startswith("globus:"):
                            m = re.search(r"^globus:([^/]*)(.*/)[^/]*$", url)
                            href = f"https://app.globus.org/file-manager?origin_id={m[1]}&origin_path={m[2]}"
                            assets = {
                                "globus": {
                                    "href": href,
                                    "description": "Globus Web App Link",
                                    "type": "text/html",
                                    "roles": ["data"],
                                    "alternate:name": dataset_doc.get("data_node"),
                                    "created": doc.get("timestamp", now),
                                    "updated": doc.get("timestamp", now),
                                    "protocol": "globus",
                                    #                                    "node" : dataset_doc.get("data_node"),
                                    "file:local_path": drspath,
                                    f"{namespace}:tracking_id": dataset_doc.get("pid"),
                                }
                            }
                    break

        size = 0
        if "HTTPServer" in dataset_doc.get("access"):
            counter = 0

            for doc in json_data:
                if doc.get("type") == "File":
                    urls = doc.get("url")
                    for url in urls:
                        if url.endswith("application/netcdf|HTTPServer"):
                            url_split = url.split("|")
                            href = url_split[0]
                            checksum_type = doc.get("checksum_type", "SHA256")
                            if checksum_type != "SHA256":
                                raise RuntimeError(f"{checksum_type} not supported")
                            checksum = doc.get("checksum", None)
                            if not checksum:
                                raise RuntimeError(f"Checksum not found for {doc.get('title')}")

                            assets[doc.get("title", f"data{counter:04}")] = {
                                "href": href,
                                "description": "HTTPServer Link",
                                "type": "application/netcdf",
                                "roles": ["data"],
                                "alternate:name": dataset_doc.get("data_node"),
                                "file:size": doc.get("size", 0),
                                "file:checksum": f"1220{checksum}",
                                f"{namespace}:tracking_id": doc.get("tracking_id"),
                                "created": doc.get("timestamp", now),
                                "updated": doc.get("timestamp", now),
                                "protocol": "https",
                                # "node" : dataset_doc.get("data_node"),
                                "file:local_path": f"{drspath}/{doc.get('title')}",
                            }
                            size += doc.get("size", 0)
                            counter += 1
                            break

        if not assets:
            self.publog.error(f"No assets found for {item_id}")
            return None

        west_degrees = float(dataset_doc.get("west_degrees", -180.0))
        south_degrees = float(dataset_doc.get("south_degrees", -90.0))
        east_degrees = float(dataset_doc.get("east_degrees", 180.0))
        north_degrees = float(dataset_doc.get("north_degrees", 90.0))

        # STAC needs longitude in range [-180, 180], but CF might use [0, 360)

        if abs(east_degrees - west_degrees - 360) < 1e-3:
            # represent any global range (e.g. 0 to 360 or -180 to 180 in the data)
            # as -180 to 180
            west_degrees, east_degrees = -180., 180.
        else:
            # otherwise force each value separately to range [-180, 180) (for west)
            # or (-180, 180] (for east)
            west_degrees = (west_degrees + 180) % 360 - 180
            east_degrees = (east_degrees + 180) % 360 - 180

            if east_degrees == -180.:
                east_degrees = 180.

        if south_degrees < -90.:
            func = self.publog.info if south_degrees > -90.001 else self.publog.warning
            func(f"forcing min lat {south_degrees} into range (-90)")
            south_degrees = -90.

        if north_degrees > 90.:
            func = self.publog.info if north_degrees < 90.001 else self.publog.warning
            func(f"forcing max lat {north_degrees} into range (90)")
            north_degrees = 90.

        dt_start = dataset_doc.get("datetime_start", None)
        dt_end = dataset_doc.get("datetime_end", None)
        properties = {"size": size, "created": now, "updated": now, "retracted": False}
        if dt_start and dt_end:
            properties["datetime"] = None
            properties["start_datetime"] = dt_start
            properties["end_datetime"] = dt_end
        else:

            properties["datetime"] = None
            properties["start_datetime"] = "1850-01-01T00:00:00Z"
            properties["end_datetime"] = "1850-01-01T00:00:01Z"

        if namespace == "cmip6plus":
            collection_key_name = "CMIP6"
        else:
            collection_key_name = collection

        collection_item_properties = STAC_proj_item_properties.get(
            collection_key_name.lower(), []
        )
        stac_keys = STAC_item_properties + collection_item_properties

        # STAC keys are the end result keys, now just define how to get them.
        for k in stac_keys:
            v = None

            # if using map_properties legacy, map to legacy properties

            LEGACY_properties = MAP_properties
            sp = SOURCE_properties.get(collection_key_name.lower(),{})

            if k in LEGACY_properties.get(collection_key_name,{}):
                mapped_k = LEGACY_properties[collection_key_name][k]
                v = dataset_doc.get(mapped_k, None)

            # Use esgvoc to construct source mappings
            elif k in sp:
                sourced_k, required = SOURCE_properties[collection_key_name.lower()][k]
                v = dataset_doc.get(sourced_k,None)

                if v is None and required:
                    self.publog.error(f'Property "{sourced_k}" is required in source.')
            else:
                self.publog.warning(f"{k} not found in dataset")

            if k == "master_id":
                nk = "base_id"
            elif k in STAC_item_properties:
                nk = k
            elif k in collection_item_properties:
                nk = f"{namespace}:{k}"
            if isinstance(v, list):

                if k in STAC_list_properties["ALL"]:
                    properties[nk] = v
                elif (
                    collection_key_name in STAC_list_properties
                    and k in STAC_list_properties[collection_key_name]
                ):
                    properties[nk] = v
                else:
                    if v[0] is None:
                        continue
                    properties[nk] = v[0]
            elif v is not None:
                properties[nk] = v
        try:
            esgvoc_version = jsg.get_schema_version(namespace)
        except AttributeError:
            esgvoc_version = ""
            self.publog.warning(
                "esgvoc json schema generator does not support schema version lookup"
            )
        except Exception:
            esgvoc_version = ""
            self.publog.warning(
                f"{namespace} not in esgvoc db, did you remember to 'use' this?"
            )

        # Prefer the schema version from the user's selected esgvoc database.
        # Fall back to configured versions only when esgvoc cannot provide one.
        sc_version = esgvoc_version or STAC_schema_versions.get(collection, "")
        if sc_version == "":
            self.publog.error(f"Collection {namespace} not configured")
            return None

        item = {
            "type": "Feature",
            "stac_version": "1.1.0",
            "stac_extensions": [
                # "https://stac-extensions.github.io/cmip6/v3.0.0/schema.json",
                f"https://esgf.github.io/stac-transaction-api/{namespace}/{sc_version}/schema.json",
                # "http://host.docker.internal/cmip6/v2.0.2/schema.json",
                "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json",
                # "http://host.docker.internal/alternate-assets/v1.2.0/schema.json",
                "https://stac-extensions.github.io/file/v2.1.0/schema.json",
                # "http://host.docker.internal/file/v2.1.0/schema.json"
            ],
            "id": item_id,
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [west_degrees, south_degrees],
                        [east_degrees, south_degrees],
                        [east_degrees, north_degrees],
                        [west_degrees, north_degrees],
                        [west_degrees, south_degrees],
                    ]
                ],
            },
            "bbox": [west_degrees, south_degrees, east_degrees, north_degrees],
            "collection": collection,
            "links": [
                {
                    "rel": "self",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{collection}/items/{item_id}",
                },
                {
                    "rel": "parent",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{collection}",
                },
                {
                    "rel": "collection",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{collection}",
                },
                {
                    "rel": "root",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections",
                },
            ],
            "properties": properties,
            "assets": assets,
        }

        if "citation_url" in dataset_doc:
            item["links"].append(self.citation_link_d(dataset_doc["citation_url"]))
        else:
            print("WARNING no Citation url")

        # Pulled directly from dataset_doc
        for aggregation_type in AGGREGATED_ASSETS:
            if aggregation_type in dataset_doc:
                item["assets"][aggregation_type] = dataset_doc[aggregation_type]

                # Separately configure for adding aggregated_assets schema.

        return item
