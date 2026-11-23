#!/usr/bin/env python
"""
Script to reduce NetCDF file size for test fixtures while preserving metadata.
"""
import xarray as xr
import sys
from pathlib import Path

def examine_file(filepath):
    """Print file structure and size information."""
    ds = xr.open_dataset(filepath)

    print(f"File: {filepath}")
    print(f"File size: {Path(filepath).stat().st_size / 1e6:.2f} MB")
    print(f"\nDimensions:")
    for dim, size in ds.dims.items():
        print(f"  {dim}: {size}")

    print(f"\nData variables:")
    for var in ds.data_vars:
        shape = ds[var].shape
        dtype = ds[var].dtype
        print(f"  {var}: {shape} ({dtype})")

    print(f"\nCoordinate variables:")
    for coord in ds.coords:
        shape = ds[coord].shape
        dtype = ds[coord].dtype
        print(f"  {coord}: {shape} ({dtype})")

    print(f"\nGlobal attributes (sample):")
    attrs_to_show = ['project', 'domain', 'experiment', 'institution',
                     'driving_model', 'source', 'frequency']
    for attr in attrs_to_show:
        if attr in ds.attrs:
            print(f"  {attr}: {ds.attrs[attr]}")

    ds.close()
    return ds.dims

def reduce_file(input_path, output_path, time_slice=2, lat_slice=5, lon_slice=5):
    """
    Reduce NetCDF file size by subsetting dimensions.

    Parameters:
    - time_slice: number of time steps to keep
    - lat_slice: number of latitude points to keep
    - lon_slice: number of longitude points to keep
    """
    ds = xr.open_dataset(input_path)

    # Subset to minimal dimensions
    subset_params = {}
    if 'time' in ds.dims:
        subset_params['time'] = slice(0, time_slice)
    if 'lat' in ds.dims:
        subset_params['lat'] = slice(0, lat_slice)
    if 'lon' in ds.dims:
        subset_params['lon'] = slice(0, lon_slice)
    if 'rlat' in ds.dims:  # CORDEX uses rotated pole coordinates
        subset_params['rlat'] = slice(0, lat_slice)
    if 'rlon' in ds.dims:
        subset_params['rlon'] = slice(0, lon_slice)
    if 'x' in ds.dims:
        subset_params['x'] = slice(0, lon_slice)
    if 'y' in ds.dims:
        subset_params['y'] = slice(0, lat_slice)

    ds_stub = ds.isel(subset_params)

    # Apply compression to all data variables
    encoding = {}
    for var in ds_stub.data_vars:
        encoding[var] = {'zlib': True, 'complevel': 9}
    for coord in ds_stub.coords:
        if coord not in ds_stub.dims:  # Don't encode dimension coordinates
            encoding[coord] = {'zlib': True, 'complevel': 9}

    # Save with compression
    ds_stub.to_netcdf(output_path, encoding=encoding)

    original_size = Path(input_path).stat().st_size / 1e6
    reduced_size = Path(output_path).stat().st_size / 1e6
    reduction_pct = (1 - reduced_size / original_size) * 100

    print(f"\n{'='*60}")
    print(f"Reduction complete!")
    print(f"Original size: {original_size:.2f} MB")
    print(f"Reduced size:  {reduced_size:.2f} MB")
    print(f"Reduction:     {reduction_pct:.1f}%")
    print(f"Output:        {output_path}")

    ds.close()
    ds_stub.close()

if __name__ == "__main__":
    input_file = "tests/unit/data/CORDEX-CMIP6/DD/NAM-25/CCCma/CanESM5-1/historical/r1i1p1f2/CanRCM5-SN/v1-r2/mon/tas/v20260903/tas_NAM-25_CanESM5-1_historical_r1i1p1f2_CCCma_CanRCM5-SN_v1-r2_mon_195001-195012.nc"

    print("="*60)
    print("EXAMINING ORIGINAL FILE")
    print("="*60)
    dims = examine_file(input_file)

    output_file = input_file.replace(".nc", "_stub.nc")

    print(f"\n{'='*60}")
    print("REDUCING FILE SIZE")
    print("="*60)
    reduce_file(input_file, output_file, time_slice=2, lat_slice=5, lon_slice=5)
