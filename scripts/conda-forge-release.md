# Conda-Forge Release Instructions

This guide covers one-off conda-forge releases. For automated releases, see the end of this document.

## Prerequisites

- PyPI release must be published first
- GitHub account with 2FA enabled
- Conda-forge feedstock repository access (or ability to fork)

## One-Off Release Process

### Step 1: Check if esgcet feedstock exists

```bash
# Check if feedstock exists
open https://github.com/conda-forge/esgcet-feedstock

# If it doesn't exist, you'll need to create it first (see "Initial Feedstock Creation" below)
```

### Step 2: Fork and clone the feedstock

```bash
# Fork via GitHub UI, then:
git clone https://github.com/YOUR-USERNAME/esgcet-feedstock
cd esgcet-feedstock
git remote add upstream https://github.com/conda-forge/esgcet-feedstock
```

### Step 3: Update the recipe

Edit `recipe/meta.yaml`:

```yaml
{% set version = "5.5.2" %}  # ← Update this

package:
  name: esgcet
  version: {{ version }}

source:
  url: https://pypi.io/packages/source/e/esgcet/esgcet-{{ version }}.tar.gz
  sha256: {{ SHA256_HASH }}  # ← Update this (see below)

build:
  number: 0  # ← Reset to 0 for new version
  script: {{ PYTHON }} -m pip install . -vv
  noarch: python

requirements:
  host:
    - python >=3.11
    - pip
    - setuptools
  run:
    - python >=3.11
    # Copy dependencies from pyproject.toml [project.dependencies]
    - xarray
    - netcdf4
    - pyyaml
    # ... etc

test:
  imports:
    - esgcet
  commands:
    - esgpublish --version

about:
  home: https://github.com/ESGF/esg-publisher
  license: BSD-3-Clause
  license_file: LICENSE
  summary: 'Earth System Grid Federation (ESGF) publication tool'
  description: |
    Publishing client for ESGF publisher
  doc_url: https://esg-publisher.readthedocs.io/
  dev_url: https://github.com/ESGF/esg-publisher
```

### Step 4: Get SHA256 hash

```bash
# Download the source from PyPI
VERSION=5.5.2
curl -LO https://pypi.io/packages/source/e/esgcet/esgcet-${VERSION}.tar.gz

# Calculate SHA256
shasum -a 256 esgcet-${VERSION}.tar.gz
# Or on Linux:
# sha256sum esgcet-${VERSION}.tar.gz

# Copy the hash and update meta.yaml
```

### Step 5: Test locally (optional but recommended)

```bash
# Install conda-build
conda install conda-build

# Build the package
conda build recipe/

# Test in a fresh environment
conda create -n test-esgcet python=3.12
conda activate test-esgcet
conda install --use-local esgcet
esgpublish --version
conda deactivate
```

### Step 6: Push and create PR

```bash
git checkout -b v5.5.2
git add recipe/meta.yaml
git commit -m "Update to version 5.5.2"
git push origin v5.5.2
```

Then create a Pull Request:
1. Go to https://github.com/YOUR-USERNAME/esgcet-feedstock
2. Click "Contribute" → "Open pull request"
3. Title: `Update to version 5.5.2`
4. Description:
   ```
   Updates esgcet to version 5.5.2
   
   Release notes: https://github.com/ESGF/esg-publisher/releases/tag/v5.5.2
   PyPI: https://pypi.org/project/esgcet/5.5.2/
   
   Changes:
   - Updated version to 5.5.2
   - Updated SHA256 hash
   - Reset build number to 0
   ```

### Step 7: Wait for CI and review

- Conda-forge bots will automatically run CI tests
- Address any failures
- Once CI passes, conda-forge maintainers will review
- After approval and merge, package will be available on conda-forge in ~1 hour

### Step 8: Verify release

```bash
# Wait for package to be available, then:
conda search esgcet -c conda-forge
conda install esgcet=5.5.2 -c conda-forge
```

---

## Initial Feedstock Creation

If the esgcet feedstock doesn't exist yet:

### Step 1: Use staged-recipes

```bash
git clone https://github.com/conda-forge/staged-recipes
cd staged-recipes
git checkout -b add-esgcet
```

### Step 2: Create recipe

```bash
cp -r recipes/example recipes/esgcet
# Edit recipes/esgcet/meta.yaml (same format as above)
```

### Step 3: Submit to staged-recipes

```bash
git add recipes/esgcet
git commit -m "Add esgcet recipe"
git push origin add-esgcet
```

Create PR to conda-forge/staged-recipes. After approval, conda-forge will:
- Create the esgcet-feedstock repository
- Add you as a maintainer
- Publish the initial version

---

## Automated Conda-Forge Releases (Future Enhancement)

### Option 1: regro-cf-autotick-bot

The conda-forge bot automatically detects new PyPI releases and creates PRs. To enable:

1. Ensure feedstock exists
2. Add maintainers to `recipe/meta.yaml`:
   ```yaml
   extra:
     recipe-maintainers:
       - your-github-username
   ```
3. The bot will auto-create PRs for new versions
4. Review and merge the bot PRs

### Option 2: GitHub Action in this repo

Create `.github/workflows/update-conda.yml`:

```yaml
name: Update Conda-Forge

on:
  release:
    types: [published]

jobs:
  update-conda-forge:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger conda-forge update
        uses: regro/cf-scripts@master
        with:
          feedstock: esgcet-feedstock
        env:
          GITHUB_TOKEN: ${{ secrets.CONDA_FORGE_TOKEN }}
```

This requires setting up a GitHub token with permissions to the feedstock.

---

## Troubleshooting

**Problem**: CI fails with "Package doesn't satisfy requirements"

**Solution**: Ensure all dependencies in `recipe/meta.yaml` match `pyproject.toml`

**Problem**: SHA256 mismatch

**Solution**: Re-download the tarball and recalculate hash. Ensure using PyPI tarball, not GitHub.

**Problem**: Tests fail

**Solution**: Add missing test dependencies to `test.requires` in meta.yaml

---

## Quick Reference Commands

```bash
# Get SHA256 of PyPI release
curl -sL https://pypi.org/pypi/esgcet/5.5.2/json | jq -r '.urls[] | select(.packagetype=="sdist") | .digests.sha256'

# Test conda package locally
conda build recipe/
conda create -n test python=3.12
conda install --use-local esgcet

# Clean up build artifacts
conda build purge
```

---

## Maintainer Contacts

- Primary: (your email)
- Conda-forge team: https://github.com/orgs/conda-forge/teams
- Help: https://conda-forge.org/docs/maintainer/updating_pkgs.html
