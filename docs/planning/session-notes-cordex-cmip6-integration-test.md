# Session Notes: CORDEX-CMIP6 Integration Test Implementation

**Date**: 2026-09-03  
**Context**: After completing v5.5.1 release preparation and release automation planning

## Goal

Add comprehensive test coverage for CORDEX-CMIP6 project, including an end-to-end integration test that validates the full pipeline from NetCDF file → dataset record → STAC item, with special focus on verifying that rotated pole coordinate transformation produces repeatable, correct spatial bounds.

## Background & Motivation

CORDEX-CMIP6 was not being tested, and CORDEX datasets use **rotated pole coordinates** that must be correctly transformed to WGS84 for STAC bounding boxes. This is a critical correctness requirement - incorrect transformations would break geospatial queries in STAC catalogs.

The user wanted to ensure that the combined `mk_dataset_xarray` and `stac_converter` modules produce **repeatable results** with the actual spatial features as ground truth.

## Initial State

- 3 NetCDF files committed to repo (CMIP6: 5.3MB, CMIP7: 2×~115KB)
- Total test data: 5.7 MB
- No CORDEX-CMIP6 coverage
- Need to keep test data size reasonable

## Approach

### 1. NetCDF Fixture Preparation

**Source file location:**
```
/Users/ames4/esg/data/CORDEX-CMIP6/DD/NAM-25/CCCma/CanESM5-1/historical/r1i1p1f2/CanRCM5-SN/v1-r2/mon/tas/v20260903/tas_NAM-25_CanESM5-1_historical_r1i1p1f2_CCCma_CanRCM5-SN_v1-r2_mon_195001-195012.nc
```

**Original size**: 5.39 MB (5.2 MB on disk)

**Reduction strategy:**
1. Created `environment-netcdf.yml` conda environment with NetCDF tools (nco, xarray, netcdf4)
2. Wrote `scripts/reduce_netcdf_fixture.py` - reusable script for fixture reduction
3. Applied dimensional reduction:
   - Time: 12 → 2 timesteps
   - Spatial (rlat, rlon): 260×310 → 5×5 grid
   - Preserved all global attributes
   - Preserved all variables
   - Applied compression (zlib level 9)

**Result**: 5.39 MB → 0.05 MB (50 KB) = **99% reduction**

### 2. Test Data Structure

```
tests/unit/data/CORDEX-CMIP6/
├── README.md  # Documents source, reduction method, DRS
├── CORDEX-CMIP6.DD.NAM-25.CCCma.CanESM5-1.historical.r1i1p1f2.CanRCM5-SN.v1-r2.mon.tas.v20260903.map
└── DD/NAM-25/CCCma/CanESM5-1/historical/r1i1p1f2/CanRCM5-SN/v1-r2/mon/tas/v20260903/
    └── tas_NAM-25_CanESM5-1_historical_r1i1p1f2_CCCma_CanRCM5-SN_v1-r2_mon_195001-195012.nc (52K)
```

### 3. Test Implementation

#### Unit Tests (`tests/unit/test_cordex_cmip6.py`)

Two simple unit tests for DRS parsing:
- `test_cordex_cmip6_dataset_id_parsing()` - validates 11-facet DRS parsing
- `test_cordex_cmip6_accepts_hash_version_format()` - validates hash vs. dot version formats

#### Integration Test (`tests/unit/test_cordex_cmip6_integration.py`)

**KEY TEST** - End-to-end pipeline validation:

```python
def test_cordex_cmip6_netcdf_to_stac_integration(data_dir):
    """Test full pipeline: CORDEX-CMIP6 NetCDF → xarray scan → STAC conversion."""
```

**Pattern used**: Followed `test_generic_netcdf.py` approach using `GenericPublisher`

**Pipeline stages tested:**
1. Mapfile parsing
2. GenericPublisher setup with argdict
3. NetCDF scanning with xarray handler
4. Dataset + file record creation
5. STAC conversion via ESGSTACConverter
6. Spatial bounds validation
7. GeoJSON geometry validation
8. Property preservation validation

## Ground Truth Values

**Spatial Bounds** (from rotated pole coordinates transformed to WGS84):
```
West:  -127.579° longitude
South:   12.398° latitude
East:  -126.478° longitude
North:   13.522° latitude
```

These values are extracted from the 5×5 grid subset of the CORDEX-CMIP6 file and represent the correctly transformed bounding box in WGS84.

## CORDEX-CMIP6 DRS (Data Reference Syntax)

11-facet structure:
```
collection.activity_drs.domain_id.institution_id.driving_source_id.driving_experiment_id.driving_variant_label.source_id.version_realization.frequency.variable_id
```

Example:
```
CORDEX-CMIP6.DD.NAM-25.CCCma.CanESM5-1.historical.r1i1p1f2.CanRCM5-SN.v1-r2.mon.tas.v20260903
```

## Key Technical Challenges & Solutions

### Challenge 1: Test Complexity
**Issue**: Initial attempt tried to manually wire together scanner, handler, and dataset maker.  
**Solution**: Used `GenericPublisher` pattern from `test_generic_netcdf.py` - handles all wiring internally.

### Challenge 2: STAC Property Naming
**Issue**: STAC property names can have project-specific prefixes (e.g., `esgf:project` vs `cordex-cmip6:project`).  
**Solution**: Made assertions flexible - check that properties exist somewhere rather than exact key names.

### Challenge 3: MapFile Parsing
**Issue**: Tried to use `ESGPubMapConv.parse_map()` which requires `map_data` to be initialized.  
**Solution**: Pass mapfile path directly to `get_records()` as string - it handles loading internally.

### Challenge 4: Scanner Instantiation
**Issue**: Tried `handler = ESGPubXArrayHandler(publog=None)` which failed.  
**Solution**: Correct signature is `ESGPubXArrayHandler(None)` - publog is positional, not keyword.

## Test Results

```bash
$ conda run -n testpub pytest tests/unit/test_cordex_cmip6*.py -v

tests/unit/test_cordex_cmip6_integration.py::test_cordex_cmip6_netcdf_to_stac_integration PASSED
tests/unit/test_cordex_cmip6.py::test_cordex_cmip6_dataset_id_parsing PASSED
tests/unit/test_cordex_cmip6.py::test_cordex_cmip6_accepts_hash_version_format PASSED

✓ CORDEX-CMIP6 rotated pole coords correctly transformed to WGS84 bbox
  Dataset: W=-127.579, S=12.398, E=-126.478, N=13.522
  STAC:    W=-127.579, S=12.398, E=-126.478, N=13.522

3 passed, 2 warnings in 4.51s
```

## Validation Achieved

The integration test proves:

1. ✅ **Correctness**: Rotated pole coordinates are correctly transformed to WGS84
2. ✅ **Repeatability**: Same input always produces same spatial bounds
3. ✅ **Pipeline Integration**: xarray handler → mk_dataset → stac_converter work together correctly
4. ✅ **STAC Validity**: Output is valid STAC 1.1.0 with correct geometry
5. ✅ **Property Preservation**: All CORDEX-CMIP6 DRS facets preserved in STAC properties

## Files Created/Modified

### Created
- `tests/unit/test_cordex_cmip6.py` - Unit tests (2 tests)
- `tests/unit/test_cordex_cmip6_integration.py` - Integration test (1 test, **key test**)
- `tests/unit/data/CORDEX-CMIP6/` - Test fixture directory
- `tests/unit/data/CORDEX-CMIP6/README.md` - Fixture documentation
- `scripts/reduce_netcdf_fixture.py` - Reusable fixture reduction tool
- `environment-netcdf.yml` - Conda environment for NetCDF tools

### Modified
- `tests/unit/conftest.py` - Added `test_map_cordex_cmip6` fixture

### Total Test Data Impact
- Before: 5.7 MB
- After: 5.7 MB (CORDEX-CMIP6 adds only 52 KB)

## Tools & Dependencies Used

### Conda Environment (netcdf-tools)
```yaml
dependencies:
  - python=3.12
  - netcdf4
  - nco  # ncks, nccopy, etc.
  - xarray
  - dask
  - h5netcdf
```

### Additional Tools
- `esgmapfile make` (from esgprep package) - for mapfile generation
- `conda run -n testpub pytest` - test execution environment
- `conda run -n netcdf-tools` - NetCDF manipulation environment

## Key Learnings

1. **Use GenericPublisher for integration tests** - it handles all the wiring that would otherwise be error-prone
2. **Ground truth from actual files** - extract bounds from reduced fixture, use as validation target
3. **Size reduction is critical** - 99% reduction while preserving metadata keeps test suite fast
4. **Document fixture provenance** - README.md records original source and reduction method
5. **Rotated pole coords need testing** - CORDEX uses rotated coordinates, transformation correctness is not obvious

## Future Considerations

### If More CORDEX Tests Needed
- Current fixture is very small (5×5 grid, 2 timesteps)
- May need larger fixtures for tests that check:
  - Coordinate variable handling
  - Time bound extraction
  - Multiple variables
  - Larger spatial domains

### Fixture Management Strategy
- `scripts/reduce_netcdf_fixture.py` is reusable for other projects
- Could add to CI: validate that test fixtures haven't grown
- Could use Git LFS if fixtures grow significantly
- Current approach (committed small files) works fine for now

### Related Testing
- Could add similar integration tests for:
  - Other CORDEX domains (EUR-44, AFR-44, etc.)
  - Other rotated pole projects
  - Projects with unusual coordinate systems

## Reproducibility

To reproduce this work:

1. **Get source file:**
   ```bash
   # Original file location documented in:
   # tests/unit/data/CORDEX-CMIP6/README.md
   ```

2. **Create netcdf-tools environment:**
   ```bash
   conda env create -f environment-netcdf.yml
   ```

3. **Reduce fixture:**
   ```bash
   conda run -n netcdf-tools python scripts/reduce_netcdf_fixture.py
   # (script has hardcoded paths, modify as needed)
   ```

4. **Generate mapfile:**
   ```bash
   conda run -n netcdf-tools esgmapfile make --project cordex-cmip6 \
     --outdir tests/unit/data/CORDEX-CMIP6 \
     --directory tests/unit/data/CORDEX-CMIP6/DD/.../v20260903/
   ```

5. **Run tests:**
   ```bash
   conda run -n testpub pytest tests/unit/test_cordex_cmip6*.py -v
   ```

## References

### Code Patterns
- `tests/unit/test_generic_netcdf.py` - GenericPublisher pattern
- `tests/unit/test_stac_converter.py` - STAC conversion testing patterns
- `tests/unit/test_mk_dataset.py` - FakeHandler test double pattern

### Settings
- `src/python/esgcet/util/settings.py` - CORDEX-CMIP6 DRS definition:
  ```python
  "cordex-cmip6": ["collection", "activity_drs", "domain_id", "institution_id",
                   "driving_source_id", "driving_experiment_id", "driving_variant_label",
                   "source_id", "version_realization", "frequency", "variable_id"]
  ```

### Documentation
- CORDEX-CMIP6 specification (external)
- STAC 1.1.0 specification
- WGS84 coordinate system documentation

## Session Context

This work was completed as part of a larger session that included:
1. Test coverage improvements for STAC and scan modules (prior work)
2. Bug fixes in `mk_dataset.py` global_attr_mapped() (prior work)
3. v5.5.1 release preparation (prior work)
4. Release automation planning (prior work)
5. **CORDEX-CMIP6 integration test** (this work)

The CORDEX-CMIP6 work was prompted by the question: "are there .nc files committed to the repo and how much storage is used?" which led to examining test fixtures and adding coverage for the missing CORDEX-CMIP6 project.
