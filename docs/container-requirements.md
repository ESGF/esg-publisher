# Container Requirements for esgcet

**Status**: Design Document (Not Yet Implemented)

This document defines requirements for a containerized deployment of esgcet. The goal is to simplify deployment while maintaining flexibility for different institutional configurations.

---

## Core Principles

1. **No Running Services**: esgcet is a batch/CLI tool, not a daemon
   - Container runs a command and exits
   - No background processes or exposed ports
   - Suitable for one-off runs, cron jobs, or workflow orchestration

2. **Minimal User Configuration**: Pre-populate sensible defaults
   - Users only specify their site-specific settings
   - Container merges user config with built-in defaults
   - Validation and helpful error messages

3. **Data Access via Mounts**: No data copied into container
   - User mounts their data directories read-only
   - User mounts config directory for persistence
   - Optional: mount output directory for logs/artifacts

---

## Container Architecture

### Base Image

```dockerfile
FROM mambaorg/micromamba:latest
# or
FROM continuumio/miniconda3:latest
```

**Requirements:**
- Python 3.11+
- Small footprint
- Fast package installation

### Installed Components

**Core:**
- esgcet package (from PyPI or conda-forge)
- All runtime dependencies
- Basic CLI tools (curl, jq, git for debugging)

**Optional:**
- Pre-downloaded CV files (esgvoc)
- Common QA/QC checker configs
- Example configuration templates

---

## Volume Mounts

### Required Mounts

**1. Data Directory** (read-only)
```bash
-v /path/to/data:/data:ro
```
- Contains NetCDF files to publish
- Mounted read-only for safety
- Can have multiple data mounts for different projects

**2. Config Directory** (read-write)
```bash
-v ~/.esg:/home/esgcet/.esg
```
- Contains `esg.yaml` user configuration
- Container writes logs here
- Persists credentials/cache

### Optional Mounts

**3. Output Directory** (read-write)
```bash
-v /path/to/output:/output
```
- For `--save-stac` outputs
- Mapfiles
- Kerchunk references

**4. Certificates** (read-only, if needed)
```bash
-v /path/to/certs:/certs:ro
```
- For custom CA certificates
- ESGF node certificates

---

## Configuration Strategy

### Built-in Default Config (`/app/config/default.yaml`)

Pre-populated with common settings:

```yaml
# Sensible defaults that work for most users
log_level: INFO
dry_run: false
no_xarray: false

# Empty but structured for user override
data_roots: {}
mountpoints: {}

# Common service endpoints (can be overridden)
index_nodes:
  esgf-node.llnl.gov: {}

# Pre-configured handlers
handlers:
  - cmip6
  - cmip7
  - cordex-cmip6
```

### User Config (`/home/esgcet/.esg/esg.yaml`)

User provides only their site-specific settings:

```yaml
# Minimal user config - only what they need
data_node: esgf-data.mysite.edu
index_node: esgf-node.llnl.gov

data_roots:
  /data/cmip6: cmip6_root

mountpoints:
  /data: /mnt/storage

globus:
  endpoint_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Config Merge Strategy

Container startup script merges configs:

```bash
#!/bin/bash
# /app/entrypoint.sh

# 1. Copy default config if user config doesn't exist
if [ ! -f /home/esgcet/.esg/esg.yaml ]; then
  echo "Creating default config from template..."
  mkdir -p /home/esgcet/.esg
  cp /app/config/default.yaml /home/esgcet/.esg/esg.yaml
  echo "Edit /home/esgcet/.esg/esg.yaml with your settings"
  exit 1
fi

# 2. Validate required fields
python /app/scripts/validate-config.py /home/esgcet/.esg/esg.yaml

# 3. Run esgcet command
exec esgpublish "$@"
```

---

## Usage Examples

### Interactive Setup (First Run)

```bash
# Create config directory
mkdir -p ~/.esg

# Run container to generate template
docker run --rm \
  -v ~/.esg:/home/esgcet/.esg \
  esgf/esgcet:5.5.3

# Edit generated config
vim ~/.esg/esg.yaml

# Now ready for actual publishing
```

### Publishing Data

```bash
docker run --rm \
  -v /data/cmip6:/data:ro \
  -v ~/.esg:/home/esgcet/.esg \
  esgf/esgcet:5.5.3 \
  esgpublish --project CMIP6 /data/CMIP6.NCAR.CESM2.historical.map
```

### Dry Run / Validation

```bash
docker run --rm \
  -v /data/cmip6:/data:ro \
  -v ~/.esg:/home/esgcet/.esg \
  esgf/esgcet:5.5.3 \
  esgpublish --dry-run --project CMIP6 /data/CMIP6.*.map
```

### Save STAC Items to Output Directory

```bash
docker run --rm \
  -v /data/cmip6:/data:ro \
  -v ~/.esg:/home/esgcet/.esg \
  -v /output:/output \
  esgf/esgcet:5.5.3 \
  esgpublish --save-stac --project CMIP6 /data/CMIP6.*.map
```

---

## Environment Variables

Container supports environment variable overrides:

```bash
docker run --rm \
  -e ESG_CONFIG_FILE=/home/esgcet/.esg/esg.yaml \
  -e ESGCET_LOG_LEVEL=DEBUG \
  -e ESGCET_DRY_RUN=true \
  -v /data:/data:ro \
  -v ~/.esg:/home/esgcet/.esg \
  esgf/esgcet:5.5.3 \
  esgpublish /data/*.map
```

**Supported Variables:**
- `ESG_CONFIG_FILE` - Config file path (default: `~/.esg/esg.yaml`)
- `ESGCET_LOG_LEVEL` - Logging level (default: `INFO`)
- `ESGCET_DRY_RUN` - Dry run mode (default: `false`)
- `ESGCET_DATA_NODE` - Override data node
- `ESGCET_INDEX_NODE` - Override index node

---

## Orchestration Examples

### Docker Compose

```yaml
version: '3.8'

services:
  esgcet:
    image: esgf/esgcet:5.5.3
    volumes:
      - /data/cmip6:/data:ro
      - ~/.esg:/home/esgcet/.esg
      - /output:/output
    environment:
      - ESGCET_LOG_LEVEL=INFO
    command: esgpublish --project CMIP6 /data/CMIP6.*.map
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: esgcet-publisher
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: esgcet
            image: esgf/esgcet:5.5.3
            args:
            - esgpublish
            - --project
            - CMIP6
            - /data/CMIP6.*.map
            volumeMounts:
            - name: data
              mountPath: /data
              readOnly: true
            - name: config
              mountPath: /home/esgcet/.esg
            env:
            - name: ESGCET_LOG_LEVEL
              value: INFO
          volumes:
          - name: data
            hostPath:
              path: /data/cmip6
          - name: config
            persistentVolumeClaim:
              claimName: esgcet-config
          restartPolicy: OnFailure
```

### Slurm Batch Job

```bash
#!/bin/bash
#SBATCH --job-name=esgcet-publish
#SBATCH --output=esgcet-%j.log
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

module load singularity

singularity exec \
  --bind /data/cmip6:/data:ro \
  --bind $HOME/.esg:/home/esgcet/.esg \
  docker://esgf/esgcet:5.5.3 \
  esgpublish --project CMIP6 /data/CMIP6.*.map
```

---

## Security Considerations

### User/Group ID Mapping

Container should run as non-root and respect host UID/GID:

```dockerfile
# In Dockerfile
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} esgcet && \
    useradd -u ${USER_ID} -g esgcet -m esgcet

USER esgcet
```

**Usage:**
```bash
docker run --rm \
  --user $(id -u):$(id -g) \
  -v /data:/data:ro \
  -v ~/.esg:/home/esgcet/.esg \
  esgf/esgcet:5.5.3 \
  esgpublish /data/*.map
```

### Read-only Root Filesystem

```bash
docker run --rm \
  --read-only \
  --tmpfs /tmp \
  -v /data:/data:ro \
  -v ~/.esg:/home/esgcet/.esg \
  esgf/esgcet:5.5.3 \
  esgpublish /data/*.map
```

### Credential Management

**Option 1: Mount credentials**
```bash
-v ~/.globus:/home/esgcet/.globus:ro
```

**Option 2: Use secrets (Kubernetes)**
```yaml
env:
- name: GLOBUS_CLIENT_ID
  valueFrom:
    secretKeyRef:
      name: globus-credentials
      key: client-id
```

**Option 3: Interactive login (not recommended for automation)**
```bash
docker run -it \
  -v ~/.esg:/home/esgcet/.esg \
  esgf/esgcet:5.5.3 \
  esglogin
```

---

## Testing Requirements

### Container Image Tests

```bash
# 1. Verify image builds
docker build -t esgf/esgcet:test .

# 2. Check installed version
docker run --rm esgf/esgcet:test esgpublish --version

# 3. Test config generation
docker run --rm -v /tmp/test-config:/home/esgcet/.esg esgf/esgcet:test

# 4. Validate with dry-run
docker run --rm \
  -v $(pwd)/tests/unit/data:/data:ro \
  -v /tmp/test-config:/home/esgcet/.esg \
  esgf/esgcet:test \
  esgpublish --dry-run /data/test.map
```

### Integration Tests

- Test with each supported project (CMIP6, CMIP7, CORDEX-CMIP6)
- Test with different mount configurations
- Test error handling (missing config, bad paths)
- Test permissions (read-only data, read-write config)

---

## Distribution

### Container Registries

**Primary:**
- Docker Hub: `docker.io/esgf/esgcet:5.5.3`
- GitHub Container Registry: `ghcr.io/esgf/esg-publisher:5.5.3`

**Mirrored at:**
- Quay.io: `quay.io/esgf/esgcet:5.5.3` (optional)

### Tagging Strategy

```
esgf/esgcet:latest          # Latest stable release
esgf/esgcet:5.5.3           # Specific version
esgf/esgcet:5.5             # Minor version
esgf/esgcet:5               # Major version
esgf/esgcet:dev             # Development build from main
```

### Multi-architecture Support

Build for multiple platforms:
```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t esgf/esgcet:5.5.3 .
```

---

## Implementation Checklist

When implementing, create these files:

- [ ] `docker/Dockerfile` - Main container definition
- [ ] `docker/entrypoint.sh` - Startup script with config merge
- [ ] `docker/default-config.yaml` - Built-in default configuration
- [ ] `docker/validate-config.py` - Config validation script
- [ ] `docker/docker-compose.yml` - Example compose file
- [ ] `docker/README.md` - Container usage documentation
- [ ] `.github/workflows/build-container.yml` - Automated builds
- [ ] Update main README with container instructions

---

## Future Enhancements

### Phase 2: Multi-site Orchestration

Support for federated publishing across sites:

```yaml
# multi-site-config.yaml
sites:
  - name: LLNL
    data_node: esgf-data1.llnl.gov
    data_mount: /data/llnl
  - name: DKRZ
    data_node: esgf-data.dkrz.de
    data_mount: /data/dkrz
```

### Phase 3: Web UI Container

Optional companion container with web UI for monitoring:
- View publishing status
- Validate configurations
- Generate mapfiles visually
- Browse STAC items

### Phase 4: Pre-built Binaries

Create single-file executables for environments without Docker:
- PyInstaller or similar
- Include Python runtime
- No container runtime required

---

## References

- Docker best practices: https://docs.docker.com/develop/dev-best-practices/
- 12-factor app: https://12factor.net/
- Conda in containers: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file
- Kubernetes batch jobs: https://kubernetes.io/docs/concepts/workloads/controllers/job/
- Singularity/Apptainer: https://apptainer.org/docs/user/main/

---

**Document Version**: 1.0  
**Last Updated**: 2026-09-17  
**Status**: Design/Planning Phase  
**Implementation**: TBD
