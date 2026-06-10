import re
from datetime import datetime

from esgcet.settings import (MAP_properties, STAC_item_properties,
                             STAC_list_properties, STAC_proj_item_properties,
                             STAC_schema_versions)


from esgvoc.apps.jsg import json_schema_generator as jsg

class ESGSTACItem():
    """
    Container class for the item with Methods to add Assets
    """
    def __init__(self, si):
        if si:
            self.stac_item = si
        else:
            return None
        

    def add_aggregate(self, aggtype, url, site):
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        value = {
                "href": url,
                "type": f"application/{aggtype}",
                "role": ["data","virtual"],
                "description": "TEST",
                "alternate:name": site,
                "created" : now,
                "updated" : now
                }

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
        
        return operations       

    def add_replica(self, rep_datanode, template, prefix, rep_globus=""):
        assets = self.stac_item.get("assets", {})
        operations = []
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")        
        for name, asset in assets.items():

            if name == "reference_file":
                continue
            
            if asset.get("alternate:name") == rep_datanode:
                continue
                               
            if rep_datanode in asset.get("alternate",{}):
                continue
    
            replica_asset = {
                "description": asset.get("description"),
                "type": asset.get("type"),
                "roles": asset.get("roles", []),
                "alternate:name": rep_datanode,
                "created" : asset("created"),
                "updated" : now
            }
            rep_path = "TEST/PATH"
            rep_path = asset.get("file:local_path", rep_path)
            
            if name == "globus":
                if not rep_globus:
                    continue
                replica_asset["href"] = (
                    f"https://app.globus.org/file-manager?"
                    f"origin_id={rep_globus}&origin_path={rep_path}"
                )
    
            elif asset.get("type") == "application/netcdf":
                replica_asset["href"] = template.format(prefix,rep_path)
            op = {  "op" : "add",
                    "path" :f"/assets/{name}/alternate/{rep_datanode}",
                    "value" : replica_asset
                 }
            operations.append(op)
        
        return operations   
 
class ESGSTACConverter():
    def __init__(self, stac_config):
        self.stac_api = stac_config.get("stac_api", "")
        

    def citation_link_d(self, url):

        return {
                    "rel": "cite-as",
          "type": "application/json",
           "href" : url
        }
    
    def convert2stac(self, json_data):
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        dataset_doc = {}
        for doc in json_data:
            if doc.get("type") == "Dataset":
                dataset_doc = doc
                break
    
        assets = {}
        item_id = dataset_doc.get("instance_id")
        drspath = item_id.replace('.','/')         
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
                                    "created" : doc.get("timestamp", now),
                                    "updated" : doc.get("timestamp", now),
                                    "protocol" : "globus",
#                                    "node" : dataset_doc.get("data_node"),
                                    "file:local_path" : drspath,
                                    f"{namespace}:tracking_id": dataset_doc.get("pid")
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
                
                            assets[doc.get("title", f"data{counter:04}")] = {
                                "href": href,
                                "description": "HTTPServer Link",
                                "type": "application/netcdf",
                                "roles": ["data"],
                                "alternate:name": dataset_doc.get("data_node"),
                                "file:size": doc.get("size", 0),
                                "file:checksum": "1220" + doc.get("checksum"),
                                f"{namespace}:tracking_id": doc.get("tracking_id"),
                                "created" : doc.get("timestamp", now),
                                "updated" : doc.get("timestamp", now),
                                "protocol" : "https",
#                                "node" : dataset_doc.get("data_node"),                               
                                "file:local_path" : f"{drspath}/{doc.get("title")}"
                            }
                            size += doc.get("size", 0)
                            counter += 1
                            break
    
        if not assets:
            return None
    
            
        west_degrees = dataset_doc.get("west_degrees", 0.0) - 180
        south_degrees = dataset_doc.get("south_degrees", -90.0)
        east_degrees = dataset_doc.get("east_degrees", 360.0) - 180
        north_degrees = dataset_doc.get("north_degrees", 90.0)
    
    
        dt_start = dataset_doc.get("datetime_start", None)
        dt_end = dataset_doc.get("datetime_end", None)
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
    
        if namespace == "cmip6plus":
            collection_key_name = "CMIP6"
        else:
            collection_key_name = collection

        collection_item_properties = STAC_proj_item_properties.get(collection_key_name, [])
        property_keys = STAC_item_properties + collection_item_properties
    
        for k in property_keys:
            if collection_key_name in MAP_properties and k in MAP_properties[collection_key_name]:
                mapped_k = MAP_properties[collection_key_name][k]
                v = dataset_doc.get(mapped_k, "")
            elif k in dataset_doc:
                v = dataset_doc.get(k, "")
            else:
                print(f"WARNING {k} not found in dataset")
            if k == "master_id":
                nk = "base_id"
            if k in STAC_item_properties:
                nk = k
            elif k in collection_item_properties:
                nk = f"{namespace}:{k}"
            if isinstance(v, list):
                
                if k in STAC_list_properties["ALL"]:
                    properties[nk] = v
                elif collection_key_name in STAC_list_properties and k in STAC_list_properties[collection_key_name]:
                    properties[nk] = v
                else:
                    if v[0] is None:
                        continue
                    properties[nk] = v[0]
            else:
                if v is None:
                    continue
                properties[nk] = v
    
        sc_version = STAC_schema_versions.get(collection, jsg.get_schema_version(namespace))
        
        
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

        if "citation_url" in dataset_doc:
            item["links"].append(self.citation_link_d(dataset_doc["citation_url"]) )
        else:
            print("WARNING no Citation url")
        return item
