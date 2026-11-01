# CORDEX-CMIP6 Test Data

## Source

Original file location:
```
/Users/ames4/esg/data/CORDEX-CMIP6/DD/NAM-25/CCCma/CanESM5-1/historical/r1i1p1f2/CanRCM5-SN/v1-r2/mon/tas/v20260903/tas_NAM-25_CanESM5-1_historical_r1i1p1f2_CCCma_CanRCM5-SN_v1-r2_mon_195001-195012.nc
```

## Size Reduction

- **Original size**: 5.39 MB
- **Reduced size**: 0.05 MB (50 KB)
- **Reduction**: 99.0%

## Reduction Method

Used `scripts/reduce_netcdf_fixture.py` to create a minimal test fixture:
- Time dimension: reduced from 12 to 2 timesteps
- Spatial dimensions (rlat, rlon): reduced from 260×310 to 5×5
- All global attributes preserved
- All variables preserved with compression (zlib level 9)

## Dataset Details

- **Project**: CORDEX-CMIP6
- **Domain**: North America (NAM-25)
- **Institution**: Canadian Centre for Climate Modelling and Analysis (CCCma)
- **Source Model**: CanRCM5-SN (Canadian Regional Climate Model version 5)
- **Driving Model**: CanESM5-1
- **Experiment**: historical
- **Variant**: r1i1p1f2
- **Frequency**: monthly (mon)
- **Variable**: tas (near-surface air temperature)
- **Version**: v20260903

## DRS

CORDEX-CMIP6 Data Reference Syntax (DRS):
```
collection.activity_drs.domain_id.institution_id.driving_source_id.driving_experiment_id.driving_variant_label.source_id.version_realization.frequency.variable_id
```

Example:
```
CORDEX-CMIP6.DD.NAM-25.CCCma.CanESM5-1.historical.r1i1p1f2.CanRCM5-SN.v1-r2.mon.tas.v20260903
```
