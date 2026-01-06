import os
from typing import Any

import esgcet.logger as logger
import requests
from esgcet import __version__
from esgcet.settings import (
    EGI_AUTH,
    STAC_CLIENT,
    STAC_TRANSACTION_API,
    TOKEN_STORAGE_FILE,
)
from globus_sdk import (
    BaseClient,
    GroupsClient,
    NativeAppAuthClient,
    RefreshTokenAuthorizer,
)
from globus_sdk.scopes import GroupsScopes
from globus_sdk.tokenstorage import SimpleJSONFileAdapter

from .egi_oauth2_device_flow import OAuthDeviceFlowPKCE

log = logger.ESGPubLogger()


class GlobusTransactionClient:
    def __init__(self, stac_api=None, verbose=False, silent=False):
        if stac_api:
            self.stac_api = stac_api
        else:
            self.stac_api = STAC_TRANSACTION_API.get("base_url")
        self.verbose = verbose
        self.silent = silent
        self.publog = log.return_logger("STAC Client", silent, verbose)
        self.scopes = [
            GroupsScopes.view_my_groups_and_memberships,
            STAC_TRANSACTION_API.get("scope_string"),
        ]
        self.auth_client = NativeAppAuthClient(
            client_id=STAC_CLIENT.get("client_id"),
            app_name="ESGF2 STAC Transaction API",
        )
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
        filename = os.path.expanduser(TOKEN_STORAGE_FILE)
        token_storage = SimpleJSONFileAdapter(filename)
        if not token_storage.file_exists():
            response = self._do_login_flow()
            token_storage.store(response)
            self.groups_tokens = response.by_resource_server[
                GroupsClient.resource_server
            ]
            self.transaction_tokens = response.by_resource_server[
                STAC_TRANSACTION_API.get("client_id")
            ]
        else:
            self.groups_tokens = token_storage.get_token_data(
                GroupsClient.resource_server
            )
            self.transaction_tokens = token_storage.get_token_data(
                STAC_TRANSACTION_API.get("client_id")
            )

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
        resp = self.transaction_client.post(
            f"{self.stac_api}/collections/{collection}/items",
            headers=headers,
            json=entry,
        )
        print("DATA", entry)
        if resp.status_code == 201:
            self.publog.info(resp.status_code)
            self.publog.info("Published")
        elif resp.status_code == 202:
            self.publog.info(resp.status_code)
            self.publog.info("Queued for publication")
        else:
            self.publog.error(f"Failed to publish: Error {resp.status_code}")


class EGITransactionClient:
    """EGI Transaction client for publishing ESGF items."""

    def __init__(self, stac_api=None, verbose=False, silent=False):
        if stac_api:
            self.stac_api = stac_api

        else:
            self.stac_api = STAC_TRANSACTION_API.get("base_url")

        self.verbose = verbose
        self.silent = silent
        self.publog = log.return_logger("STAC Client", silent, verbose)

        self.auth = OAuthDeviceFlowPKCE(
            client_id=EGI_AUTH.get("client_id"),
            client_secret=EGI_AUTH.get("client_secret"),
            device_endpoint=EGI_AUTH.get("device_url"),
            token_endpoint=EGI_AUTH.get("token_url"),
            scope=EGI_AUTH.get("scope"),
            refresh_file=os.path.expanduser(TOKEN_STORAGE_FILE),
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
                verify=EGI_AUTH.get("verify", True),
                timeout=EGI_AUTH.get("timeout", 5.0),
            )

            response.raise_for_status()

            match response.status_code:
                case 200:
                    self.publog.info("Published")

                case 202:
                    self.publog.info("Queued for publication")

        except requests.exceptions.HTTPError as err:
            self.publog.error("Failed to publish: Error %s", err.response.status_code)
