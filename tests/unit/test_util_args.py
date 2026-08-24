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
