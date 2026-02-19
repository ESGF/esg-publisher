import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from requests.auth import HTTPBasicAuth


@dataclass
class EGIConf:
    """
    Dataclass for EGI configuration.
    """

    client_id: str = "3da9c21e-2bb9-4576-9054-af420514cb7b"
    device_url: str = (
        "https://aai.egi.eu/auth/realms/egi/protocol/openid-connect/auth/device"
    )
    token_url: str = (
        "https://aai.egi.eu/auth/realms/egi/protocol/openid-connect/auth/device"
    )
    scope: str = "offline_access entitlements"
    base_url: str = "https://api.stac.esgf.ceda.ac.uk"
    verify: bool = True
    timeout: float = 5.0


class OAuthDeviceFlowPKCE:
    """
    Handles OAuth 2.0 Device Authorization Grant flow with PKCE for command-line applications.

    Features:
    - Initiates device code flow
    - Polls for access token
    - Refreshes expired tokens
    - Persists token data locally
    """

    def __init__(
        self,
        client_id: str,
        device_endpoint: str,
        token_endpoint: str,
        scope: str,
        resource: str,
        refresh_file: str = "token.json",
    ) -> None:
        """
        Initializes the OAuth Device Code Flow handler.

        Args:
            client_id (str): OAuth client ID.
            device_endpoint (str): URL to initiate device code flow.
            token_endpoint (str): URL to exchange device code or refresh token.
            scope (str): OAuth scopes to request.
            refresh_file (str): Path to store token data locally.
        """
        self.client_id = client_id
        self.device_endpoint = device_endpoint
        self.token_endpoint = token_endpoint
        self.scope = scope
        self.resource = resource
        self.refresh_file = refresh_file
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge(self.code_verifier)
        self.token_data = self._load_token()
        self._create_token_file()

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        token = self.get_access_token()
        r.headers["Authorization"] = f"Bearer {token}"
        return r

    def _create_token_file(self) -> None:
        """
        Creates a blank file with permissions 0o600 if it does not already exist.
        """
        try:
            fd = os.open(self.refresh_file, flags=os.O_CREAT | os.O_EXCL, mode=0o600)
            os.close(fd)

        except FileExistsError:
            pass

    def _generate_code_verifier(self) -> str:
        """
        Generates a secure random code verifier for PKCE.

        Returns:
            str: Base64 URL-safe encoded code verifier.
        """
        return base64.urlsafe_b64encode(os.urandom(64)).rstrip(b"=").decode("utf-8")

    def _generate_code_challenge(self, verifier: str) -> str:
        """
        Creates a code challenge from the verifier using SHA256.

        Args:
            verifier (str): The code verifier.

        Returns:
            str: Base64 URL-safe encoded code challenge.
        """
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")

    def _load_token(self) -> dict[str, Any]:
        """
        Loads token data from the local file.

        Returns:
            dict: Token data if available, else empty dict.
        """
        try:
            with open(self.refresh_file, "r", encoding="utf-8") as f:
                return json.load(f)

        except (json.decoder.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_token(self) -> None:
        """
        Saves token data to local file.
        """
        with open(self.refresh_file, "w", mode=0o600, encoding="utf-8") as f:
            json.dump(self.token_data, f)

    def initiate_device_flow(self) -> dict[str, Any]:
        """
        Starts the device code flow.

        Returns:
            dict: Response containing device_code, user_code, verification_uri, etc.
        """
        payload = {
            "client_id": self.client_id,
            "scope": self.scope,
            "resource": self.resource,
            "code_challenge": self.code_challenge,
            "code_challenge_method": "S256",
        }
        print(f"POSTING to {self.device_endpoint} ")
        response = requests.post(
            self.device_endpoint,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        device_info = response.json()

        print(
            f"Visit {device_info['verification_uri']} and enter code: {device_info['user_code']}"
        )
        print(f"Or visit {device_info['verification_uri_complete']}")

        return self.poll_for_token(
            device_code=device_info["device_code"],
            interval=device_info["interval"],
            expires_in=device_info["expires_in"],
        )

    def poll_for_token(
        self, device_code: str, interval: int, expires_in: int
    ) -> dict[str, Any]:
        """
        Polls the token endpoint until the user authorizes the device.

        Args:
            device_code (str): Device code from the authorization response.
            interval (int): Polling interval in seconds.
            expires_in (int): Time in seconds before the device code expires.

        Returns:
            dict: Token data including access_token, refresh_token, etc.

        Raises:
            TimeoutError: If polling exceeds expiration time.
            Exception: For other OAuth errors.
        """
        start_time = time.time()

        while time.time() - start_time < expires_in:
            payload = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": self.client_id,
                "code_verifier": self.code_verifier,
            }

            response = requests.post(self.token_endpoint, data=payload)

            if response.status_code == 200:
                token_data = response.json()
                token_data["expires_at"] = time.time() + token_data["expires_in"]

                if "refresh_token" in token_data and "refresh_expires_in" in token_data:
                    token_data["refresh_expires_at"] = time.time() + token_data.get(
                        "refresh_expires_in"
                    )

                self.token_data = token_data
                self._save_token()

                return token_data

            if response.status_code == 400:
                error = response.json().get("error")

                if error == "authorization_pending":
                    time.sleep(interval)

                elif error == "slow_down":
                    interval += 5
                    time.sleep(interval)

                else:
                    raise Exception(f"Error during polling: {error}")

            response.raise_for_status()

        raise TimeoutError("Device code expired before authorization.")

    def refresh_token(self) -> None:
        """
        Refreshes the access token using the refresh token or re-initiate device flow
        if refresh token expired.

        Returns:
            dict: New token data.

        Raises:
            Exception: If refresh fails.
        """
        if "refresh_token" not in self.token_data or time.time() > self.token_data.get(
            "refresh_expires_at", time.time() - 10
        ):
            print("Refresh token expired. Login required...")
            return self.initiate_device_flow()

        auth = HTTPBasicAuth(self.client_id, "")

        payload = {
            "client_id": self.client_id,
            "grant_type": "refresh_token",
            "refresh_token": self.token_data["refresh_token"],
            "scope": self.scope,
            "resource": self.resource,
        }

        response = requests.post(self.token_endpoint, data=payload, auth=auth)
        response.raise_for_status()
        token_data = response.json()

        token_data["expires_at"] = time.time() + token_data["expires_in"]

        if "refresh_token" in token_data and "refresh_expires_in" in token_data:
            token_data["refresh_expires_at"] = time.time() + token_data.get(
                "refresh_expires_in"
            )

        self.token_data = token_data
        self._save_token()

    def get_access_token(self) -> str:
        """
        Retrieves a valid access token, refreshing if expired.

        Returns:
            str: Access token.
        """
        try:
            if not self.token_data:
                self.initiate_device_flow()

            if time.time() > self.token_data.get("expires_at", 0):
                print("Access token expired. Refreshing...")
                self.refresh_token()

            return self.token_data["access_token"]

        except Exception as e:
            raise SystemExit(f"Error in EGI Authentication flow: {e}") from e
