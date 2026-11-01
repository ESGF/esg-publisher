"""Tests for STAC transaction clients."""

import json
from unittest.mock import Mock

import pytest
import requests
from esgcet.stac import stac_client
from esgcet.stac.stac_client import EGITransactionClient


@pytest.fixture
def egi_client():
    """Create an EGI client that does not require authentication."""
    client = EGITransactionClient({"stac_api": "https://stac.example.test"})
    client.publog = Mock()
    return client


def error_response(status_code, body):
    """Build a requests response whose raise_for_status method raises."""
    response = requests.Response()
    response.status_code = status_code
    response._content = body.encode()
    response.url = "https://stac.example.test/collections/CMIP6/items"
    response.request = requests.Request("POST", response.url).prepare()
    return response


def test_egi_save_stac_writes_item_before_dry_run(tmp_path, monkeypatch):
    """The EGI client saves an item locally without publishing in dry-run mode."""
    monkeypatch.chdir(tmp_path)

    def unexpected_post(*args, **kwargs):
        raise AssertionError("dry-run must not send a request")

    monkeypatch.setattr(stac_client.requests, "post", unexpected_post)
    client = EGITransactionClient(
        {
            "stac_api": "https://stac.example.test",
            "save_stac": True,
            "dry_run": True,
        }
    )
    entry = {
        "id": "CMIP6.example.dataset.v1",
        "collection": "CMIP6",
        "type": "Feature",
    }

    assert client.publish(entry) is True
    assert json.loads((tmp_path / f"{entry['id']}.json").read_text()) == entry


def test_egi_does_not_save_stac_by_default(tmp_path, monkeypatch):
    """Local persistence remains opt-in for the EGI client."""
    monkeypatch.chdir(tmp_path)
    client = EGITransactionClient(
        {
            "stac_api": "https://stac.example.test",
            "dry_run": True,
        }
    )
    entry = {"id": "CMIP6.example.dataset.v1", "collection": "CMIP6"}

    assert client.publish(entry) is True
    assert not (tmp_path / f"{entry['id']}.json").exists()


@pytest.mark.parametrize(
    "body",
    [
        '{"title":"Your request is invalid","detail":"invalid activity_id"}',
        "upstream service unavailable",
    ],
)
def test_egi_publish_logs_http_status_and_response(body, egi_client, monkeypatch):
    """Publication failures retain JSON and plain-text server diagnostics."""
    monkeypatch.setattr(
        stac_client.requests, "post", lambda *args, **kwargs: error_response(400, body)
    )

    result = egi_client.publish({"id": "dataset", "collection": "CMIP6"})

    assert result is False
    egi_client.publog.error.assert_called_once_with(
        "Failed to %s: HTTP %s; response=%s", "publish", 400, body
    )


def test_egi_update_logs_http_status_and_response(egi_client, monkeypatch):
    """Patch failures report the same server diagnostics as publication."""
    body = '{"detail":"item cannot be updated"}'
    monkeypatch.setattr(
        stac_client.requests, "patch", lambda *args, **kwargs: error_response(409, body)
    )

    result = egi_client.json_patch("CMIP6", "dataset", [])

    assert result is False
    egi_client.publog.error.assert_called_once_with(
        "Failed to %s: HTTP %s; response=%s", "update", 409, body
    )


def test_egi_http_error_without_response_uses_exception(egi_client):
    """A malformed HTTPError still produces useful diagnostics."""
    error = requests.exceptions.HTTPError("request failed without a response")

    egi_client._log_http_error("publish", error)

    egi_client.publog.error.assert_called_once_with(
        "Failed to %s: HTTP %s; response=%s",
        "publish",
        "unknown",
        "request failed without a response",
    )


@pytest.mark.parametrize(
    ("request_method", "client_method", "args", "action"),
    [
        ("post", "publish", ({"id": "dataset", "collection": "CMIP6"},), "publish"),
        ("patch", "json_patch", ("CMIP6", "dataset", []), "update"),
    ],
)
def test_egi_logs_transport_failures(
    request_method, client_method, args, action, egi_client, monkeypatch
):
    """Timeouts and other request failures produce a clean failure result."""
    error = requests.exceptions.Timeout("transaction API timed out")

    def raise_timeout(*unused_args, **unused_kwargs):
        raise error

    monkeypatch.setattr(stac_client.requests, request_method, raise_timeout)

    result = getattr(egi_client, client_method)(*args)

    assert result is False
    egi_client.publog.error.assert_called_once_with(
        f"Failed to {action}: %s", error
    )
