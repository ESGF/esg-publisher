import re
from datetime import datetime
from esgcet.settings import (
    STAC_item_properties, 
    STAC_proj_item_properties, 
    STAC_list_properties, 
    STAC_schema_versions,
    MAP_properties
)

class ESGSTACConverter():
    def __init__(self, stac_config):
        self.stac_api = stac_config.get("stac_api", "")
        

    def convert2stac(self, json_data):
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        dataset_doc = {}
        for doc in json_data:
            if doc.get("type") == "Dataset":
                dataset_doc = doc
                break
    
        assets = {}
    
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
                                    "created" : doc.get("timestamp", now),
                                    "updated" : doc.get("timestamp", now),
                                    "protocol" : "globus"
                                    
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
                            checksum_type = doc.get("checksum_type")
                            if checksum_type != "SHA256":
                                raise RuntimeError(f"{checksum_type} not supported")
                                
                            assets[doc.get("title", f"data{counter:04}")] = {
                                "href": href,
                                "description": "HTTPServer Link",
                                "type": "application/netcdf",
                                "roles": ["data"],
                                "alternate:name": dataset_doc.get("data_node"),
                                "file:size": doc.get("size", 0),
                                "file:checksum": "1220" + doc.get("checksum"),
                                "cmip6:tracking_id": doc.get("tracking_id"),
                                "created" : doc.get("timestamp", now),
                                "updated" : doc.get("timestamp", now),
    
                                "protocol" : "https"
                            }
                            size += doc.get("size", 0)
                            counter += 1
                            break
    
        if not assets:
            return None
    
    
        collection = dataset_doc.get("project")
        if collection == "mip-drs7":
            collection = "cmip7"
            
        item_id = dataset_doc.get("instance_id")
        west_degrees = dataset_doc.get("west_degrees", 0.0)
        south_degrees = dataset_doc.get("south_degrees", -90.0)
        east_degrees = dataset_doc.get("east_degrees", -360.0)
        north_degrees = dataset_doc.get("north_degrees", 90.0)
    
    
        dt_start = dataset_doc.get("datetime_start", None)
        dt_end = dataset_doc.get("datetime_start", None)
        properties = {
    
            "size": size,
            "created": now,
            "updated": now,
            "retracted" : False
        }
        if (dt_start and dt_end):
            properties["datetime"] = None
            properties["start_datetime"] = dt_start
            properties["end_datetime"] = dt_end
        else:
    
            properties["datetime"] = None
            properties["start_datetime"] = "1850-01-01T00:00:00Z"
            properties["end_datetime"] = "1850-01-01T00:00:01Z"
    
        
        collection_item_properties = STAC_proj_item_properties.get(collection, [])
        property_keys = STAC_item_properties + collection_item_properties
        namespace = collection.lower()
    
        for k in property_keys:
            if collection in MAP_properties and k in MAP_properties[collection]:
                mapped_k = MAP_properties[collection][k]
                v = dataset_doc.get(mapped_k)
            else:
                v = dataset_doc.get(k)
            if k in STAC_item_properties:
                nk = k
            elif k in collection_item_properties:
                nk = f"{namespace}:{k}"
            if isinstance(v, list):
                if k in STAC_list_properties:
                    properties[nk] = v
                else:
                    if v[0] is None or v[0] == "none":
                        continue
                    properties[nk] = v[0]
            else:
                if v is None or v == "none":
                    continue
                # SKA workaround if integer index's are wanted
                #                if "_index" in nk:
                #                    v = int(v[1:])
                if nk == "cmip7:version":
                    v = f"{v}"
                properties[nk] = v
    
        sc_version = STAC_schema_versions.get(collection)
        if not sc_version:
            raise RuntimeError(f"No version of STAC schema for {collection}")
        
        item = {
            "type": "Feature",
            "stac_version": "1.1.0",
            "stac_extensions": [
                #"https://stac-extensions.github.io/cmip6/v3.0.0/schema.json",
                 f"https://esgf.github.io/stac-transaction-api/{namespace}/{sc_version}/schema.json",               
                #"http://host.docker.internal/cmip6/v2.0.2/schema.json",
                "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json",
                #"http://host.docker.internal/alternate-assets/v1.2.0/schema.json",
                "https://stac-extensions.github.io/file/v2.1.0/schema.json"
                #"http://host.docker.internal/file/v2.1.0/schema.json"
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
                        [west_degrees, south_degrees]
                    ]
                ]
            },
            "bbox": [
                west_degrees, south_degrees, east_degrees, north_degrees
            ],
            "collection": collection,
            
            "links": [
                {
                    "rel": "self",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{collection}/items/{item_id}"
                },
                {
                    "rel": "parent",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{collection}"
                },
                {
                    "rel": "collection",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections/{collection}"
                },
                {
                    "rel": "root",
                    "type": "application/json",
                    "href": f"{self.stac_api}/collections"
                }
            ],
            "properties": properties,
            "assets": assets
        }
    
        return item
