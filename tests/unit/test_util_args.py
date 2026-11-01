"""Tests for esgcet.util.args module (PublisherArgs)."""
import pytest
from unittest.mock import patch
from esgcet.util.args import PublisherArgs


def test_get_args_basic(test_map_cmip6):
    """Test basic argument parsing."""
    pub_args = PublisherArgs()
    # --map is required, so provide it
    test_argv = ["prog", "--test", "--map", str(test_map_cmip6)]

    with patch("sys.argv", test_argv):
        args = pub_args.get_args()

    # Should return a namespace with test mode enabled
    assert hasattr(args, 'test')
    assert args.test is True
    assert hasattr(args, 'map')


def test_get_dict_cmip6(test_map_cmip6):
    """Test get_dict for CMIP6 project."""
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6)]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CMIP6')

    # Check required fields are present in argdict
    assert isinstance(argdict, dict)
    assert 'proj' in argdict
    assert 'verbose' in argdict
    assert 'silent' in argdict
    # Note: 'map' is in args namespace but not necessarily in argdict
    assert argdict['proj'] == 'CMIP6'


def test_get_dict_preserves_project_case(test_map_cmip6):
    """Test that project name case is preserved in argdict."""
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6)]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CMIP6')

    # Project should be stored as provided
    assert argdict['proj'] == 'CMIP6'


def test_no_xarray_flag(test_map_cmip6):
    """Test --no-xarray flag sets skipxr in argdict."""
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6), "--no-xarray"]

    with patch("sys.argv", test_argv):
        args = pub_args.get_args()
        argdict = pub_args.get_dict('CMIP6')

    assert args.skipxr is True
    assert argdict['skipxr'] is True


def test_dry_run_flag(test_map_cmip6):
    """Test --dry-run flag sets dry_run in argdict."""
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6), "--dry-run"]

    with patch("sys.argv", test_argv):
        args = pub_args.get_args()
        argdict = pub_args.get_dict('CMIP6')

    assert args.dry_run is True
    assert argdict['dry_run'] is True


def test_save_stac_flag(test_map_cmip6):
    """Test --save-stac flag sets save_stac in argdict."""
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6), "--save-stac"]

    with patch("sys.argv", test_argv):
        args = pub_args.get_args()
        argdict = pub_args.get_dict('CMIP6')

    assert args.save_stac is True
    assert argdict['save_stac'] is True


def test_stac_api_flag(test_map_cmip6):
    """Test --stac-api flag sets stac_api in argdict."""
    pub_args = PublisherArgs()
    test_api_url = "https://test.stac.api/v1"
    test_argv = ["prog", "--map", str(test_map_cmip6), "--stac-api", test_api_url]

    with patch("sys.argv", test_argv):
        args = pub_args.get_args()
        argdict = pub_args.get_dict('CMIP6')

    assert args.stac_api == test_api_url
    assert argdict.get('stac_api') == test_api_url


def test_config_file_skipxr_default(test_map_cordex_cmip6, tmp_path):
    """Test that skipxr can be set via config file."""
    pub_args = PublisherArgs()

    # Create a minimal config with skipxr: true
    # Use CORDEX-CMIP6 to avoid cmor_path requirement
    config_content = """
data_node: test.node
data_roots:
  /test: test_root
skipxr: true
"""
    config_file = tmp_path / "test_skipxr.yaml"
    config_file.write_text(config_content)

    test_argv = ["prog", "--map", str(test_map_cordex_cmip6), "--config", str(config_file)]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CORDEX-CMIP6')

    # Config file setting should be used when CLI flag not provided
    assert argdict['skipxr'] is True


def test_config_file_dry_run_default(test_map_cordex_cmip6, tmp_path):
    """Test that dry_run can be set via config file."""
    pub_args = PublisherArgs()

    # Create a minimal config with dry_run: true
    config_content = """
data_node: test.node
data_roots:
  /test: test_root
dry_run: true
"""
    config_file = tmp_path / "test_dryrun.yaml"
    config_file.write_text(config_content)

    test_argv = ["prog", "--map", str(test_map_cordex_cmip6), "--config", str(config_file)]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CORDEX-CMIP6')

    # Config file setting should be used when CLI flag not provided
    assert argdict['dry_run'] is True


def test_config_file_save_stac_default(test_map_cordex_cmip6, tmp_path):
    """Test that save_stac can be set via config file."""
    pub_args = PublisherArgs()

    # Create a minimal config with save_stac: true
    config_content = """
data_node: test.node
data_roots:
  /test: test_root
save_stac: true
"""
    config_file = tmp_path / "test_savestac.yaml"
    config_file.write_text(config_content)

    test_argv = ["prog", "--map", str(test_map_cordex_cmip6), "--config", str(config_file)]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CORDEX-CMIP6')

    # Config file setting should be used when CLI flag not provided
    assert argdict['save_stac'] is True


def test_cli_flag_overrides_config_file(test_map_cordex_cmip6, tmp_path):
    """Test that CLI flags override config file settings."""
    pub_args = PublisherArgs()

    # Create a config with dry_run: false
    config_content = """
data_node: test.node
data_roots:
  /test: test_root
dry_run: false
save_stac: false
"""
    config_file = tmp_path / "test_override.yaml"
    config_file.write_text(config_content)

    # But provide CLI flags that set them to true
    test_argv = ["prog", "--map", str(test_map_cordex_cmip6), "--config", str(config_file),
                 "--dry-run", "--save-stac"]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CORDEX-CMIP6')

    # CLI flags should override config file
    assert argdict['dry_run'] is True
    assert argdict['save_stac'] is True
