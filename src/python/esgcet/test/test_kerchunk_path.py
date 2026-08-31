#!/usr/bin/env python
"""
Test dataset-id auto-generation from path for kerchunk CLI.
"""

from pathlib import Path
from esgcet.cli.kerchunk import generate_dataset_id_from_path, normalize_backend

def test_backend_normalization():
    """Test backend name normalization."""
    print("\nTesting backend normalization:")
    print("=" * 60)

    test_cases = [
        ("vz", "virtualizarr"),
        ("VZ", "virtualizarr"),
        ("virtualizarr", "virtualizarr"),
        ("Virtualizarr", "virtualizarr"),
        ("kerchunk", "kerchunk"),
        ("Kerchunk", "kerchunk"),
    ]

    for input_val, expected in test_cases:
        result = normalize_backend(input_val)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        print(f"{status}: normalize_backend('{input_val}') = '{result}' (expected: '{expected}')")

def test_dataset_id_generation():
    """Test dataset-id generation logic."""

    # Example data_roots from config
    data_roots = {
        "/Users/ames4/datatree": "data",
        "/data/cmip6": "cmip6_root",
        "/archive/project": "archive"
    }

    # Test cases
    test_cases = [
        {
            "path": "/Users/ames4/datatree/CMIP6/CMIP/E3SM-Project/E3SM-2-1/historical",
            "expected": "CMIP6.CMIP.E3SM-Project.E3SM-2-1.historical"
        },
        {
            "path": "/data/cmip6/institution/model/experiment",
            "expected": "institution.model.experiment"
        },
        {
            "path": "/archive/project/mydata/subset",
            "expected": "mydata.subset"
        }
    ]

    print("Testing dataset-id generation:")
    print("=" * 60)

    for i, test in enumerate(test_cases, 1):
        path = Path(test["path"])
        expected = test["expected"]

        try:
            result = generate_dataset_id_from_path(path, data_roots)
            status = "✓ PASS" if result == expected else "✗ FAIL"
            print(f"\nTest {i}: {status}")
            print(f"  Path:     {path}")
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")
        except Exception as e:
            print(f"\nTest {i}: ✗ ERROR")
            print(f"  Path:  {path}")
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("\nExample usage with the CLI:")
    print("  # Auto-generate dataset-id from path:")
    print("  esgcet kerchunk generate --path /Users/ames4/datatree/CMIP6/data/files/")
    print()
    print("  # Use virtualizarr backend with abbreviation:")
    print("  esgcet kerchunk generate --path /data/myfiles/ --backend vz")
    print()
    print("  # Explicitly provide dataset-id:")
    print("  esgcet kerchunk generate --path /data/myfiles/ --dataset-id my.custom.id")
    print()
    print("  # Specify custom config file:")
    print("  esgcet kerchunk generate --path /data/myfiles/ --config /path/to/config.yaml")

if __name__ == "__main__":
    test_backend_normalization()
    test_dataset_id_generation()
