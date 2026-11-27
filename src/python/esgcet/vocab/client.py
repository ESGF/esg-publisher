import os
import json
from esgcet import __version__
from esgcet.util import logger
from esgcet.util.egi_oauth2_device_flow import EGIConf, OAuthDeviceFlowPKCE
import requests
from typing import Any

log = logger.ESGPubLogger()


class EGITransactionClient:
    """EGI Transaction client for publishing ESGF items."""

    def __init__(self, 
                 stac_config: dict, 
                 verbose: bool = False, silent: bool = False,
                 dry_run: bool = False, save_stac: bool = False):

        self.dry_run   = dry_run
        self.save_stac = save_stac

        self.publog = log.return_logger("STAC VOC Client", silent, verbose)

        self.egi_conf = EGIConf(**stac_config['stac_transaction_api'])
        self.stac_api = self.egi_conf.base_url

        token_storage_file = stac_config.get("token_storage_file")

        self.auth = OAuthDeviceFlowPKCE(
            client_id=self.egi_conf.client_id,
            client_secret=self.egi_conf.client_secret,
            device_endpoint=self.egi_conf.device_endpoint,
            token_endpoint=self.egi_conf.token_endpoint,
            scope_endpoint=self.egi_conf.scope_endpoint,
            resource=self.stac_api,
            refresh_file=os.path.expanduser(token_storage_file),
        )

    def publish(self, 
                entry: dict[str, Any],
                publisher_label: str = 'esg_publisher',
                local_cache: str = '.') -> None:
        """Publish an item to the EGI authenticated STAC endpoint.

        Args:
            entry (dict[str, Any]): entry to be published
        """
        collection = entry.get("collection")
        headers = {
            "User-Agent": f"{publisher_label}/{__version__}",
        }

        if self.save_stac:
            with open(f"{local_cache}/{entry['id']}.json", "w") as f:
                f.write(json.dumps(entry, indent=1))

        if self.dry_run:
            self.publog.info("Dry-run mode: Not publishing")
            return True

        try:
            self.publog.info(f'Posting to {self.stac_api}/collections/{collection}')
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
                case 201:
                    self.publog.info("Published")
                    return True

                case 202:
                    self.publog.info("Queued for publication")
                    return True

        except requests.exceptions.HTTPError as err:
            self.publog.error("Failed to publish: Error %s", err.response.status_code)
            self.publog.debug(f'Error response: {err.response.content}')
            return False
        return True

    def json_patch(self, collection, item_id, entry):
        """Publish an update to the EGI authenticated STAC endpoint.

        Args:
            entry (dict[str, Any]): entry to be published
        """

        headers = {
            "User-Agent": f"esgf_publisher/{__version__}",
            "Content-Type": "application/json-patch+json",
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
                    return True

                case 202:
                    self.publog.info("Queued for update")
                    return True

        except requests.exceptions.HTTPError as err:
            self.publog.error("Failed to update: Error %s", err.response.status_code)
            return err.response.content