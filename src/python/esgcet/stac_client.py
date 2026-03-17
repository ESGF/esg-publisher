import json
import os
from typing import Any

import esgcet.logger as logger
import requests
from esgcet import __version__
from esgcet.settings import *

from globus_sdk import (
    BaseClient,
    GroupsClient,
    NativeAppAuthClient,
    RefreshTokenAuthorizer,
)
from globus_sdk.scopes import GroupsScopes
from globus_sdk.tokenstorage import SimpleJSONFileAdapter

from .egi_oauth2_device_flow import EGIConf, OAuthDeviceFlowPKCE

log = logger.ESGPubLogger()


class GlobusTransactionClient:
    def __init__(self, args):
        verbose = args.get("verbose", False)
        silent = args.get("silent", False)
        self.publog = log.return_logger("STAC Client", silent, verbose)

        self.stac_config = args.get("stac_config", None)

        if not self.stac_config:
            self.publog.exception("STAC client not configured")
            exit(1)
        transaction_api = self.stac_config.get("stac_transaction_api", None)
        if not transaction_api:
            self.publog.exception("Misconfig of STAC client")
            exit(1)
        self.stac_api = transaction_api.get(
            "base_url", STAC_TRANSACTION_API.get("base_url")
        )

        self.trans_client_id = transaction_api.get(
            "client_id", STAC_TRANSACTION_API.get("client_id")
        )

        scope_string = transaction_api.get(
            "scope_string", STAC_TRANSACTION_API.get("scope_string")
        )
        self.scopes = [GroupsScopes.view_my_groups_and_memberships, scope_string]
        print(f"DEBUG {self.scopes} ")
        stac_client_id = args.get("stac_config")["stac_client"].get(
            "client_id", STAC_CLIENT.get("client_id")
        )
        self.auth_client = NativeAppAuthClient(
            client_id=stac_client_id, app_name="ESGF2 STAC Transaction API"
        )
        self.dry_run = args.get("dry_run")
        self._create_clients()

    def _do_login_flow(self):
        self.auth_client.oauth2_start_flow(
            requested_scopes=self.scopes,
            refresh_tokens=True,
        )
        authorize_url = self.auth_client.oauth2_get_authorize_url()
        print("Please go to this URL and login: {0}".format(authorize_url))
        auth_code = input("Please enter the code here: ").strip()
        return self.auth_client.oauth2_exchange_code_for_tokens(auth_code)

    def _create_clients(self):
        token_storage_file = self.stac_config.get(
            "token_storage_file", TOKEN_STORAGE_FILE
        )
        filename = os.path.expanduser(token_storage_file)
        token_storage = SimpleJSONFileAdapter(filename)
        if not token_storage.file_exists():
            response = self._do_login_flow()
            token_storage.store(response)

            self.groups_tokens = response.by_resource_server[
                GroupsClient.resource_server
            ]
            self.transaction_tokens = response.by_resource_server[self.trans_client_id]
        else:
            self.groups_tokens = token_storage.get_token_data(
                GroupsClient.resource_server
            )
            self.transaction_tokens = token_storage.get_token_data(self.trans_client_id)

        groups_authorizer = RefreshTokenAuthorizer(
            self.groups_tokens["refresh_token"],
            self.auth_client,
            access_token=self.groups_tokens["access_token"],
            expires_at=self.groups_tokens["expires_at_seconds"],
            on_refresh=token_storage.on_refresh,
        )
        self.groups_client = GroupsClient(
            authorizer=groups_authorizer,
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
            authorizer=transaction_authorizer,
        )

    def get_my_groups(self):
        groups = self.groups_client.get_my_groups()
        return groups

    def publish(self, entry):
        collection = entry.get("collection")
        headers = {
            "User-Agent": f"esgf_publisher/{__version__}",
        }
        with open(f"{entry["id"]}.json", "w") as f:
            f.write(json.dumps(entry, indent=1))

        if not self.dry_run:
            resp = self.transaction_client.post(
                f"/collections/{collection}/items", headers=headers, data=entry
            )
            if resp.http_status == 201:
                self.publog.info(resp.http_status)
                self.publog.info("Published")
            elif resp.http_status == 202:
                self.publog.info(resp.http_status)
                self.publog.info("Queued for publication")
            else:
                self.publog.error(f"Failed to publish: Error {resp.http_status}")

    def json_patch(self, collection, item_id, entry):
        """
        RFC 6902 https://tools.ietf.org/html/rfc6902
        JSON Patch is a format for describing changes to a JSON document
        in a way that is similar to a diff
        It consists of a sequence of operations to be applied to the target JSON document
        """
        headers = {
            "Content-Type": "application/json-patch+json",
            "User-Agent": f"test_client/{__version__}",
        }
#        entry = { "operations" : entry }
        print(f"DEBUG {collection} {item_id} {entry}")
        if self.dry_run:
            print("Not PATCHing (dry-run mode)")
            return
        resp = self.transaction_client.patch(f"/collections/{collection}/items/{item_id}", headers=headers, data=entry)
        if resp.http_status == 201:
            print(resp.http_status)
            print("Updated (JSON PATCH)")
            return True
        elif resp.http_status == 202:
            print(resp.http_status)
            print("Queued for update (JSON PATCH)")
            return True
        else:
            print(f"Failed to update (JSON PATCH): Error {resp.http_status}")
            return False


class EGITransactionClient:
    """EGI Transaction client for publishing ESGF items."""

    def __init__(self, args):
        verbose = args.get("verbose", False)
        silent = args.get("silent", False)
        self.publog = log.return_logger("STAC Client", silent, verbose)

        self.stac_config = args.get("stac_config", None)
        if not self.stac_config:
            self.publog.exception("STAC client not configured")
            exit(1)

        transaction_api = self.stac_config.get("stac_transaction_api", {})
        self.egi_conf = EGIConf(**transaction_api)

        self.stac_api = self.egi_conf.base_url

        token_storage_file = self.stac_config.get(
            "token_storage_file", TOKEN_STORAGE_FILE
        )

        self.auth = OAuthDeviceFlowPKCE(
            client_id=self.egi_conf.client_id,
            device_endpoint=self.egi_conf.device_endpoint,
            token_endpoint=self.egi_conf.token_endpoint,
            scope=self.egi_conf.scope,
            resource=self.stac_api,
            refresh_file=os.path.expanduser(token_storage_file),
        )

    def publish(self, entry: dict[str, Any]) -> None:
        """Publish an item to the EGI authenticated STAC endpoint.

        Args:
            entry (dict[str, Any]): entry to be published
        """
        collection = entry.get("collection")
        headers = {
            "User-Agent": f"esgf_publisher/{__version__}",
        }

        try:
            response = requests.post(
                f"{self.stac_api}/collections/{collection}/items",
                headers=headers,
                json=entry,
                auth=self.auth,
                verify=self.egi_conf.verify,
                timeout=self.egi_conf.timeout,
            )

            response.raise_for_status()

            match response.status_code:
                case 200:
                    self.publog.info("Published")

                case 202:
                    self.publog.info("Queued for publication")

        except requests.exceptions.HTTPError as err:
            self.publog.error("Failed to publish: Error %s", err.response.status_code)

    def json_patch(self, collection, item_id, entry):
        """Publish an update to the EGI authenticated STAC endpoint.

        Args:
            entry (dict[str, Any]): entry to be published
        """

        headers = {
            "User-Agent": f"esgf_publisher/{__version__}",
        }

        try:
            response = requests.patch(
                f"{self.stac_api}/collections/{collection}/items/{item_id}",
                headers=headers,
                json=entry,
                auth=self.auth,
                verify=self.egi_conf.verify,
                timeout=self.egi_conf.timeout,
            )

            response.raise_for_status()

            match response.status_code:
                case 201:
                    self.publog.info("Updated")

                case 202:
                    self.publog.info("Queued for update")

        except requests.exceptions.HTTPError as err:
            self.publog.error("Failed to update: Error %s", err.response.status_code)

def getTransactionClient(stac_config):
    sc = stac_config.get("stac_client", {})
    
    if "globus" in sc.get("redirect_uri", ""):
        auth = "Globus"
    else:
        auth = "EGI"
    res = (
        EGITransactionClient if auth == "EGI" else GlobusTransactionClient
    )
    return res