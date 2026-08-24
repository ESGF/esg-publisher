from pathlib import Path
import pytest
import os

@pytest.fixture
def data_dir():
    return Path(__file__).parent / "data"

@pytest.fixture(scope="session", autouse=True)
def initialize_esgvoc():
    """
    Initialize esgvoc for test session.

    Note: Users are expected to have esgvoc initialized before running the publisher,
    as it's required for compliance-checking and esgprep workflows. This fixture
    ensures esgvoc is available during test runs.

    Requires both universe (for DRS validation) and cmip6 (for project specs).
    """
    try:
        import subprocess
        # Initialize universe database (required for DRS validation in kerchunk tests)
        for db in ["universe@latest", "cmip6@latest"]:
            result = subprocess.run(
                ["esgvoc", "use", db],
                capture_output=True,
                text=True,
                timeout=30,
                check=False  # Don't raise on non-zero exit
            )
            if result.returncode != 0 and result.stderr:
                # Log warning but don't fail - esgvoc might already be initialized
                print(f"esgvoc initialization warning for {db}: {result.stderr}")
    except Exception as e:
        # esgvoc might not be installed in dev environments
        print(f"Could not initialize esgvoc: {e}")
    yield

@pytest.fixture
def esgvoc_available():
    """Check if esgvoc is initialized and available for CMIP6."""
    try:
        import esgvoc.api as ev
        # Check if cmip6 database is active
        info = ev.get_active_database_info('cmip6')
        return info is not None
    except Exception:
        return False

@pytest.fixture
def test_config_file(data_dir):
    """Provide path to test configuration file."""
    return data_dir / "test_esg_config.yaml"

@pytest.fixture(autouse=True)
def setup_test_environment(test_config_file, monkeypatch):
    """Set up test environment with config file."""
    # Set environment variable to point to test config
    monkeypatch.setenv("ESG_CONFIG_FILE", str(test_config_file))
    # Also create a mock ~/.esg directory if tests look for it
    yield

@pytest.fixture
def test_map_cmip6(data_dir):
    test_map = (
        data_dir
        / "CMIP6/CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast.s2017-r1i1p1f1.Amon.psl.gn.v20210114.map"
    )
    return test_map

@pytest.fixture
def test_map_cmip7(data_dir):
    test_map = (
        data_dir
       #/ "MIP-DRS7/MIP-DRS7.CMIP7.CMIP.CCCma.CanESM6-MR.historical.r2i1p1f3.glb.mon.pr.tavg-u-hxy-u.g99.v20260114.map"
       / "MIP-DRS7/MIP-DRS7.CMIP7.CMIP.MOHC.UKESM1-0-LL.1pctCO2.r1i1p1f3.glb.mon.tas.tavg-h2m-hxy-u.g99.v20260123.map"
       #/ "MIP-DRS7/MIP-DRS7.CMIP7.CMIP.MOHC.UKESM1-0-LL.1pctCO2.r1i1p1f3.glb.mon.pr.tavg-u-hxy-u.g99.v20260123.map"
    )
    return test_map

