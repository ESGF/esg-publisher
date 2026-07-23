#!/usr/bin/env python3
"""
Refactor imports after esgcet directory reorganization.

This script updates import statements in moved files to reflect their new locations.
It systematically replaces old import paths with new ones based on the reorganization.
"""

import sys
import re
from pathlib import Path

# Mapping of old module names to their new locations
IMPORT_MAP = {
    # Project handlers (moved to project/)
    'from esgcet.generic_pub import': 'from esgcet.project.generic_pub import',
    'from esgcet.generic_netcdf import': 'from esgcet.project.generic_netcdf import',
    'from esgcet.cmip5 import': 'from esgcet.project.cmip5 import',
    'from esgcet.cmip6 import': 'from esgcet.project.cmip6 import',
    'from esgcet.e3sm import': 'from esgcet.project.e3sm import',
    'from esgcet.input4mips import': 'from esgcet.project.input4mips import',
    'from esgcet.create_ip import': 'from esgcet.project.create_ip import',

    # Solr backend (moved to solr/)
    'from esgcet.index_pub import': 'from esgcet.solr.index_pub import',
    'from esgcet.pub_client import': 'from esgcet.solr.pub_client import',
    'from esgcet.search_check import': 'from esgcet.solr.search_check import',
    'from esgcet.update_solr import': 'from esgcet.solr.update_solr import',
    'from esgcet.unpublish_solr import': 'from esgcet.solr.unpublish_solr import',
    'from esgcet.unpublish_base import': 'from esgcet.solr.unpublish_base import',
    'from esgcet.xmlfix import': 'from esgcet.solr.xmlfix import',

    # STAC backend (moved to stac/)
    'from esgcet.stac_client import': 'from esgcet.stac.stac_client import',
    'from esgcet.stac_converter import': 'from esgcet.stac.stac_converter import',
    'from esgcet.update_stac import': 'from esgcet.stac.update_stac import',
    'from esgcet.unpublish_stac import': 'from esgcet.stac.unpublish_stac import',

    # Globus backend (moved to globus/)
    'from esgcet.globus_search import': 'from esgcet.globus.globus_search import',
    'from esgcet.globus_query import': 'from esgcet.globus.globus_query import',
    'from esgcet.update_globus import': 'from esgcet.globus.update_globus import',
    'from esgcet.unpublish_globus import': 'from esgcet.globus.unpublish_globus import',

    # Metadata scanning (moved to scan/)
    'from esgcet.handler_base import': 'from esgcet.scan.handler_base import',
    'from esgcet.mk_dataset import': 'from esgcet.scan.mk_dataset import',
    'from esgcet.mk_dataset_autoc import': 'from esgcet.scan.mk_dataset_autoc import',
    'from esgcet.mk_dataset_xarray import': 'from esgcet.scan.mk_dataset_xarray import',
    'from esgcet.mk_dataset_nc4 import': 'from esgcet.scan.mk_dataset_nc4 import',
    'from esgcet.mkd_cmip5 import': 'from esgcet.scan.mkd_cmip5 import',
    'from esgcet.mkd_create_ip import': 'from esgcet.scan.mkd_create_ip import',
    'from esgcet.mkd_input4mips import': 'from esgcet.scan.mkd_input4mips import',
    'from esgcet.mkd_non_nc import': 'from esgcet.scan.mkd_non_nc import',

    # Utilities (moved to util/)
    'from esgcet.args import': 'from esgcet.util.args import',
    'from esgcet.logger import': 'from esgcet.util.logger import',
    'from esgcet.settings import': 'from esgcet.util.settings import',
    'from esgcet.mapfile import': 'from esgcet.util.mapfile import',
    'from esgcet.activity_check import': 'from esgcet.util.activity_check import',
    'from esgcet.list2json import': 'from esgcet.util.list2json import',
    'from esgcet.egi_oauth2_device_flow import': 'from esgcet.util.egi_oauth2_device_flow import',
    'from esgcet.update import': 'from esgcet.util.update import',
    'from esgcet.update_base import': 'from esgcet.util.update_base import',
    'from esgcet.pid_cite_pub import': 'from esgcet.util.pid_cite_pub import',

    # Module-style imports (import esgcet.X as Y)
    'import esgcet.logger': 'import esgcet.util.logger as logger',
    'import esgcet.settings': 'import esgcet.util.settings as settings',
    'import esgcet.args': 'import esgcet.util.args as args',
    'import esgcet.mapfile': 'import esgcet.util.mapfile as mapfile',
}

def refactor_file(file_path):
    """Refactor imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = []

        # Apply each replacement
        for old_import, new_import in IMPORT_MAP.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes.append(f"  {old_import} → {new_import}")

        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ {file_path}")
            for change in changes:
                print(change)
            return True

        return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}", file=sys.stderr)
        return False

def main():
    """Main entry point."""
    base_dir = Path('src/python/esgcet')

    # Process files in each subdirectory
    subdirs = ['cli', 'project', 'solr', 'stac', 'globus', 'scan', 'util']

    print("Refactoring imports in moved files...")
    print("=" * 70)

    total_files = 0
    updated_files = 0

    for subdir in subdirs:
        subdir_path = base_dir / subdir
        if not subdir_path.exists():
            continue

        print(f"\n📁 {subdir}/")
        print("-" * 70)

        for py_file in sorted(subdir_path.glob('*.py')):
            if py_file.name == '__init__.py':
                continue

            total_files += 1
            if refactor_file(py_file):
                updated_files += 1

    # Also check pub_internal.py at root
    pub_internal = base_dir / 'pub_internal.py'
    if pub_internal.exists():
        print(f"\n📁 root/")
        print("-" * 70)
        total_files += 1
        if refactor_file(pub_internal):
            updated_files += 1

    print("\n" + "=" * 70)
    print(f"Summary: Updated {updated_files}/{total_files} files")

    if updated_files > 0:
        print("\n✓ Import refactoring complete!")
        print("Next: Review changes with 'git diff' before committing")
    else:
        print("\n• No import changes needed")

if __name__ == '__main__':
    main()
