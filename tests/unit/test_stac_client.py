"""Tests for STAC transaction clients."""

import json

from esgcet.stac import stac_client
from esgcet.stac.stac_client import EGITransactionClient


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
