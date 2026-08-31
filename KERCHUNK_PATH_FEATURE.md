# Kerchunk CLI - Path Argument Feature

## Overview

The kerchunk CLI now supports generating kerchunk reference files directly from a directory of NetCDF files using the `--path` argument, in addition to the existing mapfile-based approach.

## New Features

### 1. Direct Path Processing

Process all `.nc` files in a directory without needing to create a mapfile first:

```bash
esgcet kerchunk generate --path /data/myproject/experiment/files/
```

### 2. Auto-Generated Dataset IDs

The CLI can automatically generate dataset IDs from the directory path structure using the `data_roots` configuration:

**How it works:**
1. Loads the config file (default: `~/.esg/esg.yaml`)
2. Finds matching prefix from `data_roots` dictionary
3. Converts the remaining path to a dataset-id by replacing `/` with `.`

**Example:**

Given this config (`esg.yaml`):
```yaml
data_roots:
  /Users/ames4/datatree: data
```

And this path:
```
/Users/ames4/datatree/CMIP6/CMIP/E3SM-Project/E3SM-2-1/historical/
```

The auto-generated dataset-id would be:
```
CMIP6.CMIP.E3SM-Project.E3SM-2-1.historical
```

## Usage

### Basic Usage (Auto-generated Dataset ID)

```bash
# Uses default config at ~/.esg/esg.yaml
esgcet kerchunk generate --path /Users/ames4/datatree/CMIP6/data/files/

# Output: Auto-generated dataset-id: CMIP6.data.files
```

### With Custom Config File

```bash
esgcet kerchunk generate --path /data/myfiles/ --config /path/to/custom/esg.yaml
```

### With Explicit Dataset ID

Override auto-generation by providing a specific dataset-id:

```bash
esgcet kerchunk generate --path /data/myfiles/ --dataset-id my.custom.dataset.id
```

### With Version String

Specify a custom version (default is 'v1'):

```bash
esgcet kerchunk generate --path /data/myfiles/ --version v2
```

### Using Virtualizarr Backend

```bash
# Full name
esgcet kerchunk generate --path /data/myfiles/ --backend virtualizarr

# Or use 'vz' abbreviation
esgcet kerchunk generate --path /data/myfiles/ --backend vz
```

### Complete Example with All Options

```bash
esgcet kerchunk generate \
    --path /data/cmip6/institution/model/exp/ \
    --backend vz \
    --format parquet \
    --dataset-id cmip6.custom.id \
    --version v3 \
    --output-dir /output/refs/ \
    --source /data/cmip6 \
    --target https://esgf-node.org/thredds/fileServer/data \
    --use-dask \
    --n-workers 8 \
    --config /etc/esg/config.yaml
```

## New Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--path` | Path | None | Directory containing .nc files (mutually exclusive with mapfile_path) |
| `--backend` | String | "kerchunk" | Backend to use: "kerchunk", "virtualizarr", or "vz" (abbreviation for virtualizarr) |
| `--dataset-id` | String | Auto-generated | Dataset ID for output file naming (optional with --path) |
| `--version` | String | "v1" | Version string for output file naming |
| `--config` | Path | `~/.esg/esg.yaml` | Path to yaml config file for auto-generation |

## Configuration Requirements

For auto-generation to work, your config file must contain a `data_roots` section:

```yaml
data_roots:
  /path/to/data/root1: root1_name
  /path/to/data/root2: root2_name
  /archive/project: project_archive
```

The keys are filesystem paths (prefixes) that will be matched against the `--path` argument.

## Behavior and Validation

### Path Processing
- All `.nc` files in the directory are collected and sorted
- Files must have `.nc` extension
- Directory must contain at least one `.nc` file
- Non-recursive: only files directly in the specified directory

### Dataset ID Auto-Generation
- Requires a valid config file with `data_roots` defined
- Path must be under one of the `data_roots` prefixes
- Remaining path segments are joined with `.` (period)
- Prints the auto-generated ID for verification

### Validation
- Cannot specify both `--path` and `mapfile_path` (mutually exclusive)
- Must specify either `--path` or `mapfile_path`
- If `--path` provided without `--dataset-id`, config file is required
- If path doesn't match any `data_roots` prefix, explicit `--dataset-id` required

### Output Files
- Default output location: same directory as the .nc files
- Output filename format: `{dataset_id}.{version}.{format}`
- Override with `--output-dir` option

## Backward Compatibility

The original mapfile-based approach continues to work unchanged:

```bash
# Single mapfile
esgcet kerchunk generate /path/to/file.map

# Directory of mapfiles
esgcet kerchunk generate /path/to/mapfiles/
```

## Error Handling

### Path doesn't match data_roots
```
ValueError: Path /unknown/path does not match any data_roots prefix.
Available prefixes: ['/Users/ames4/datatree', '/data/cmip6']
```

**Solution:** Either:
1. Add the path prefix to `data_roots` in config, or
2. Provide explicit `--dataset-id`

### Config file not found
```
ValueError: Config file not found at /Users/ames4/.esg/esg.yaml.
Provide --config or --dataset-id when using --path
```

**Solution:** Either:
1. Create config file at default location, or
2. Specify config with `--config`, or
3. Provide explicit `--dataset-id`

### No .nc files found
```
ValueError: No .nc files found in /path/to/directory
```

**Solution:** Verify the directory contains `.nc` files

## Examples

### Example 1: CMIP6 Data Processing

```bash
# Directory structure:
# /data/cmip6/CMIP/E3SM-Project/E3SM-2-1/historical/Amon/tas/gr/v20240101/
#   ├── tas_Amon_E3SM-2-1_historical_r1i1p1f1_gr_185001-185912.nc
#   ├── tas_Amon_E3SM-2-1_historical_r1i1p1f1_gr_186001-186912.nc
#   └── ...

# Config: esg.yaml
# data_roots:
#   /data/cmip6: cmip6_root

esgcet kerchunk generate \
    --path /data/cmip6/CMIP/E3SM-Project/E3SM-2-1/historical/Amon/tas/gr/v20240101/ \
    --backend vz

# Result: 
# Auto-generated dataset-id: CMIP.E3SM-Project.E3SM-2-1.historical.Amon.tas.gr.v20240101
# Output file: /data/cmip6/.../CMIP.E3SM-Project.E3SM-2-1.historical.Amon.tas.gr.v20240101.v1.json
```

### Example 2: Custom Dataset ID

```bash
esgcet kerchunk generate \
    --path /scratch/temp_data/experiment_001/ \
    --dataset-id my.project.experiment.001 \
    --version v2 \
    --output-dir /results/kerchunk/
    
# Result:
# Output file: /results/kerchunk/my.project.experiment.001.v2.json
```

### Example 3: With Path Replacement for HTTP URLs

```bash
esgcet kerchunk generate \
    --path /local/data/archive/dataset/ \
    --source /local/data/archive \
    --target https://data.esgf.org/thredds/fileServer/archive \
    --format parquet

# References in the output will point to:
# https://data.esgf.org/thredds/fileServer/archive/dataset/file.nc
```

## Testing

A test script is provided to verify the dataset-id generation logic:

```bash
python test_dataset_id_generation.py
```

This will test the path-to-dataset-id conversion with various examples.

## Migration Guide

### From Mapfile Workflow

**Old workflow:**
1. Create mapfile from directory
2. Run: `esgcet kerchunk generate mapfile.map`

**New workflow:**
1. Run: `esgcet kerchunk generate --path /directory/`

### From Manual Dataset ID Creation

**Old approach:**
```bash
# Had to manually determine and specify dataset ID
esgcet kerchunk generate mapfile.map --dataset-id CMIP.ESM.hist.v1
```

**New approach:**
```bash
# Auto-generates from path structure
esgcet kerchunk generate --path /data/CMIP/ESM/hist/
# Auto-generated dataset-id: CMIP.ESM.hist
```
