import os
import argparse
import json
import re
from globus_sdk import NativeAppAuthClient, RefreshTokenAuthorizer, BaseClient, GroupsClient
from globus_sdk.scopes import GroupsScopes
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
from esgcet.settings import STAC_CLIENT, TOKEN_STORAGE_FILE, STAC_TRANSACTION_API, STAC_item_properties, STAC_proj_item_properties, STAC_list_properties
from esgcet import __version__
import esgcet.logger as logger
from datetime import datetime

log = logger.ESGPubLogger()


class TransactionClient:
    def __init__(self, args):
        verbose = args.get("verbose", False)
        silent = args.get("silent", False)
        self.publog = log.return_logger('STAC Client', silent, verbose)

        self.stac_config = args.get("stac_config", None)

        if not self.stac_config:
            self.publog.exception("STAC client not configured")
            exit(1)
        transaction_api = self.stac_config.get("stac_transaction_api", None)
        if not transaction_api:
            self.publog.exception("Misconfig of STAC client")
            exit(1)
        self.stac_api = transaction_api.get("base_url", STAC_TRANSACTION_API.get("base_url"))

        self.trans_client_id = transaction_api.get('client_id', STAC_TRANSACTION_API.get('client_id'))

        scope_string = transaction_api.get("scope_string", STAC_TRANSACTION_API.get("scope_string"))
        self.scopes = [
            GroupsScopes.view_my_groups_and_memberships,
            scope_string           
        ]
        print(f"DEBUG {self.scopes} ")
        stac_client_id = args.get("stac_config")["stac_client"].get("client_id", STAC_CLIENT.get("client_id"))
        self.auth_client = NativeAppAuthClient(
            client_id=stac_client_id,
            app_name="ESGF2 STAC Transaction API"
        )   
        self._create_clients()
        
    def _do_login_flow(self):
        self.auth_client.oauth2_start_flow(
            requested_scopes=self.scopes,
            refresh_tokens=True
        )
        authorize_url = self.auth_client.oauth2_get_authorize_url()
        print("Please go to this URL and login: {0}".format(authorize_url))
        auth_code = input("Please enter the code here: ").strip()
        return self.auth_client.oauth2_exchange_code_for_tokens(auth_code)

    def _create_clients(self):
        token_storage_file = self.stac_config.get("token_storage_file", TOKEN_STORAGE_FILE)
        filename = os.path.expanduser(token_storage_file)
        token_storage = SimpleJSONFileAdapter(filename)
        if not token_storage.file_exists():
            response = self._do_login_flow()
            token_storage.store(response)

            self.groups_tokens = response.by_resource_server[GroupsClient.resource_server]
            self.transaction_tokens = response.by_resource_server[self.trans_client_id]
        else:
            self.groups_tokens = token_storage.get_token_data(GroupsClient.resource_server)
            self.transaction_tokens = token_storage.get_token_data(self.trans_client_id)

        groups_authorizer = RefreshTokenAuthorizer(
            self.groups_tokens["refresh_token"],
            self.auth_client,
            access_token=self.groups_tokens["access_token"],
            expires_at=self.groups_tokens["expires_at_seconds"],
            on_refresh=token_storage.on_refresh,
        )
        self.groups_client = GroupsClient(
            authorizer=groups_authorizer
        )

        transaction_authorizer = RefreshTokenAuthorizer(
            self.transaction_tokens["refresh_token"],
            self.auth_client,
            access_token=self.transaction_tokens["access_token"],
            expires_at=self.transaction_tokens["expires_at_seconds"],
            on_refresh=token_storage.on_refresh,
        )
        self.transaction_client = BaseClient(
            base_url=self.stac_api,
            authorizer=transaction_authorizer
        )

    def get_my_groups(self):
        groups = self.groups_client.get_my_groups()
        return groups



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
                                
                            assets[f"data{counter:04}"] = {
                                "href": href,
                                "description": "HTTPServer Link",
                                "type": "application/netcdf",
                                "roles": ["data"],
                                "alternate:name": dataset_doc.get("data_node"),
                                "file:size": doc.get("size", 0),
                                "file:checksum": "1220" + doc.get("checksum")[0],
                                "cmip6:tracking_id": doc.get("tracking_id")[0],
                            }
                            size += doc.get("size", 0)
                            counter += 1
                            break
    
        if not assets:
            return None
    
    
        collection = dataset_doc.get("project")
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
            "updated": now
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
                properties[nk] = v
    
        item = {
            "type": "Feature",
            "stac_version": "1.1.0",
            "stac_extensions": [
                #"https://stac-extensions.github.io/cmip6/v3.0.0/schema.json",
                "https://esgf.github.io/stac-transaction-api/cmip6/v1.0.0/schema.json",
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
    

    
    def publish(self, entry):
        collection = entry.get('collection')
        headers = {
            "User-Agent": f"esgf_publisher/{__version__}",
        }
        with open(f"{entry["id"]}.json", "w") as f:
            f.write(json.dumps(entry,indent=1))

        resp = self.transaction_client.post(f"/collections/{collection}/items", headers=headers, data=entry)
        if resp.http_status == 201:
            self.publog.info(resp.http_status)
            self.publog.info("Published")
        elif resp.http_status == 202:
            self.publog.info(resp.http_status)
            self.publog.info("Queued for publication")
        else:
            self.publog.error(f"Failed to publish: Error {resp.http_status}")

    def put(self, entry):
        
        collection = entry.get("collection")
        item_id = entry.get("id")
        headers = {
            "User-Agent": f"esgf_publisher/{__version__}",
        }
        resp = self.transaction_client.put(f"/collections/{collection}/items/{item_id}", headers=headers, data=entry)
        if resp.http_status == 201:
            self.publog.info(resp.http_status)
            self.publog.info("Updated")
            return True
        elif resp.http_status == 202:
            self.publog.info(resp.http_status)
            self.publog.info("Queued for update")
            return True
        else:
            self.publog.error(f"Failed to publish: Error {resp.http_status}")
            return False
