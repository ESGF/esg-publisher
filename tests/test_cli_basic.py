"""Basic CLI tests to verify all commands work after reorganization."""
import subprocess
import pytest

CLI_COMMANDS = [
    'esgpublish',
    'esgindexpub',
    'esgupdate',
    'esgunpublish',
    'esgmapconv',
    'esgpidcitepub',
    'esglogin',
    'esgmkpubrec',
    'esgadd',
    'esgcet',
]


@pytest.mark.parametrize("command", CLI_COMMANDS)
def test_cli_help(command):
    """Test that all CLI commands can show help."""
    result = subprocess.run([command, '--help'], capture_output=True, text=True)
    assert result.returncode == 0, f"{command} --help failed with: {result.stderr}"


@pytest.mark.parametrize("command", CLI_COMMANDS)
def test_cli_version(command):
    """Test that all CLI commands can show version (if supported)."""
    result = subprocess.run([command, '--version'], capture_output=True, text=True)
    # Some commands may not have --version, so we just check it doesn't crash badly
    # Return codes: 0 = success, 2 = argparse error (no --version flag)
    assert result.returncode in [0, 2], f"{command} --version crashed with code {result.returncode}: {result.stderr}"
