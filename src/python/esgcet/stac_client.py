import os
import argparse
import json
from globus_sdk import NativeAppAuthClient, RefreshTokenAuthorizer, BaseClient, GroupsClient
from globus_sdk.scopes import GroupsScopes
from globus_sdk.tokenstorage import SimpleJSONFileAdapter
from esgcet.settings import STAC_CLIENT, TOKEN_STORAGE_FILE, STAC_TRANSACTION_API. STAC_item_properties
from esgcet import __version__
import esgcet.logger as logger


log = logger.ESGPubLogger()


class TransactionClient:
    def __init__(self, args):
        self.verbose = args.get("verbose", False)
        self.silent = silent
        self.publog = log.return_logger('STAC Client', silent, verbose)

        self.stac_config = args.get("stac_config", None)

        if not self.stac_config:
            self.publog.exception("STAC client not configured")
            exit(1)
        transaction_api = self.stac_config.get("stac_tranasction_api", {})
        self.stac_api = transaction_api.get("base_url"), STAC_TRANSACTION_API.get("base_url"))
        scope_string = STAC_TRANSACTION_API.get("scope_string")
        self.scopes = [
            GroupsScopes.view_my_groups_and_memberships,
            scope_string           
        ]
        self.client_id = args.get("stac_config"]["stac_client"].get("client_id", STAC_CLIENT.get("client_id"))
        self.auth_client = NativeAppAuthClient(
            client_id=self.client_id,
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
        token_storage_file = get("token_storage_file", TOKEN_STORAGE_FILE)
        filename = os.path.expanduser(token_storage_file)
        token_storage = SimpleJSONFileAdapter(filename)
        if not token_storage.file_exists():
            response = self._do_login_flow()
            token_storage.store(response)
            self.groups_tokens = response.by_resource_server[GroupsClient.resource_server]
            self.transaction_tokens = response.by_resource_server[self.client_id]
        else:
            self.groups_tokens = token_storage.get_token_data(GroupsClient.resource_server)
            self.transaction_tokens = token_storage.get_token_data(self.client_id)

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

    def convert2stac(json_data):
        dataset_doc = {}
        for doc in json_data:
            if doc.get("type") == "Dataset":
                dataset_doc = doc
                break
    
        collection = dataset_doc.get("project")
        item_id = dataset_doc.get("instance_id")
        west_degrees = dataset_doc.get("west_degrees", 0.0)
        south_degrees = dataset_doc.get("south_degrees", -90.0)
        east_degrees = dataset_doc.get("east_degrees", -360.0)
        north_degrees = dataset_doc.get("north_degrees", 90.0)
    
        properties = {
            "datetime": None,
            "start_datetime": dataset_doc.get("datetime_start", "1975-01-01T00:00:00Z"),
            "end_datetime": dataset_doc.get("datetime_end", "1975-01-02T00:00:00Z"),
        }
        property_keys = STAC_item_properties.get(collection)
        for k in property_keys:
            properties[k] = dataset_doc.get(k)
    
        item = {
            "type": "Feature",
            "stac_version": "1.0.0",
            "extensions": ["https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json"],
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
                    "href": f"{STAC_API}/collections/{collection}/items/{item_id}"
                },
                {
                    "rel": "parent",
                    "type": "application/json",
                    "href": f"{STAC_API}/collections/{collection}"
                },
                {
                    "rel": "collection",
                    "type": "application/json",
                    "href": f"{STAC_API}/collections/{collection}"
                },
                {
                    "rel": "root",
                    "type": "application/json",
                    "href": f"{STAC_API}/collections"
                }
            ],
            "properties": properties,
        }
    
        assets = {}
    
        globus_href = dataset_doc.get("globus_url",None)
    
        if globus_href:
            assets = {
            "globus": {
                "href": globus_href,
                "description": "Globus Web App Link",
                "type": "text/html",
                "roles": ["data"],
                "alternate:name": dataset_doc.get("data_node"),
                }
            }
        
    
        if "HTTPServer" in dataset_doc.get("access"):
            for doc in json_data:
                if doc.get("type") == "File":
                    urls = doc.get("url")
                    for url in urls:
                        if url.endswith("application/netcdf|HTTPServer"):
                            url_split = url.split("|")
                            href = url_split[0]
                            assets[doc["title"]] = {
                                "href": href,
                                "description": "HTTPServer Link",
                                "type": "application/netcdf",
                                "roles": ["data"],
                                "alternate:name": dataset_doc.get("data_node"),
                            }
                            break
    
        item["assets"] = assets
    
        return item

    
    def publish(self, entry):
        collection = entry.get('collection')
        headers = {
            "User-Agent": f"esgf_publisher/{__version__}",
        }
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
