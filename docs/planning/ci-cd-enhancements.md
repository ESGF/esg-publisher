# CI/CD Enhancement Plan

**Status**: Draft  
**Last Updated**: 2026-07-27  
**Version**: 5.5.0a (refactor branch)

## Current State

### Existing Workflows
- ✅ **test.yml** - Automated testing on Python 3.11, 3.12, 3.13
  - Runs on push to main/refactor branches
  - Runs on pull requests to main
  - Includes esgvoc initialization
  - Tests all CLI commands

## Planned Enhancements

### 1. PyPI Publishing Workflow

**File**: `.github/workflows/publish-pypi.yml`

**Trigger**: On git tags matching `v*` (e.g., v5.5.0)

**Steps**:
1. Checkout code
2. Set up Python
3. Install build tools (`build`, `twine`)
4. Build distributions (sdist + wheel)
5. Publish to PyPI using trusted publishing (OIDC)
6. Create GitHub release with artifacts

**Benefits**:
- Automated releases when tags are pushed
- No API tokens needed (uses GitHub OIDC)
- Consistent versioning between git tags and PyPI
- Build artifacts uploaded to GitHub releases

**Prerequisites**:
- Configure PyPI trusted publisher (github.com/ESGF/esg-publisher)
- Set up permissions in PyPI project settings

### 2. ReadTheDocs Configuration

**File**: `.readthedocs.yaml`

**Configuration**:
```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.12"

python:
  install:
    - method: pip
      path: .
      extra_requirements:
        - dev

sphinx:
  configuration: docs/conf.py
  fail_on_warning: true

formats:
  - pdf
  - epub
```

**Benefits**:
- Automatic documentation builds on every commit
- Version-specific docs (latest, stable, v5.5.0, etc.)
- PDF/EPUB downloads
- Searchable documentation

**Prerequisites**:
- Import project on readthedocs.org
- Link GitHub repository
- Configure webhook (automatic)

### 3. ReadTheDocs Build Workflow (Optional)

**File**: `.github/workflows/docs.yml`

**Purpose**: Validate docs build in CI before pushing to ReadTheDocs

**Trigger**: On pull requests that modify `docs/` directory

**Steps**:
1. Set up Python
2. Install Sphinx and dependencies
3. Build HTML documentation
4. Check for warnings/errors
5. Upload artifacts for preview

**Benefits**:
- Catch documentation build errors early
- PR authors can download built docs for preview
- Prevents breaking ReadTheDocs builds

### 4. Test Coverage Workflow

**File**: `.github/workflows/coverage.yml`

**Trigger**: On push to main/refactor branches

**Steps**:
1. Run tests with coverage (`pytest --cov`)
2. Generate coverage report
3. Upload to Codecov or Coveralls
4. Comment on PRs with coverage changes

**Benefits**:
- Track test coverage over time
- Identify untested code
- Prevent coverage regressions
- Visual coverage badges in README

## Implementation Order

### Phase 1 (Immediate - This PR)
1. ✅ Create `.readthedocs.yaml` configuration
2. ✅ Test documentation builds locally
3. ✅ Commit ReadTheDocs config

### Phase 2 (Pre-release)
4. ☐ Create PyPI publishing workflow
5. ☐ Test workflow on test.pypi.org first
6. ☐ Configure PyPI trusted publisher
7. ☐ Document release process

### Phase 3 (Post-release)
8. ☐ Import project on readthedocs.org
9. ☐ Configure version tags
10. ☐ Add documentation badge to README

### Phase 4 (Future)
11. ☐ Add docs validation workflow
12. ☐ Add coverage reporting
13. ☐ Consider pre-commit hooks workflow

## Detailed Workflow Specifications

### PyPI Publishing Workflow

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build distributions
        run: python -m build
      
      - name: Check distributions
        run: twine check dist/*
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
      
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

### Documentation Validation Workflow

```yaml
name: Documentation

on:
  pull_request:
    paths:
      - 'docs/**'
      - '.readthedocs.yaml'

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install sphinx sphinx-rtd-theme
      
      - name: Build HTML documentation
        run: |
          cd docs
          make html
      
      - name: Check for warnings
        run: |
          cd docs
          make html 2>&1 | tee build.log
          ! grep -i warning build.log
      
      - name: Upload documentation
        uses: actions/upload-artifact@v3
        with:
          name: documentation
          path: docs/_build/html/
```

## Testing Strategy

### Test PyPI Publishing
1. Create test tag: `git tag v5.5.0-test`
2. Push to fork: `git push origin v5.5.0-test`
3. Workflow builds and uploads to test.pypi.org
4. Verify package: `pip install -i https://test.pypi.org/simple/ esgcet==5.5.0-test`
5. Delete test tag if successful

### Test ReadTheDocs
1. Build locally: `cd docs && make html`
2. Check output: `python -m http.server -d _build/html`
3. Fix any warnings/errors
4. Push config and verify on readthedocs.org

## Release Process (After Workflows Implemented)

1. **Prepare Release**
   - Update version in `pyproject.toml`
   - Update `docs/whatsnew.rst`
   - Update README if needed
   - Commit changes

2. **Create Tag**
   ```bash
   git tag -a v5.5.0 -m "Release v5.5.0 - Package refactoring"
   git push origin v5.5.0
   ```

3. **Automated Steps** (no manual intervention)
   - GitHub Actions builds package
   - Publishes to PyPI
   - Creates GitHub release
   - ReadTheDocs builds documentation for v5.5.0

4. **Verification**
   - Check PyPI page: https://pypi.org/project/esgcet/
   - Check GitHub release: https://github.com/ESGF/esg-publisher/releases
   - Check ReadTheDocs: https://esg-publisher.readthedocs.io/

## Required Secrets/Configuration

### GitHub Secrets (None needed for OIDC publishing)
- PyPI uses trusted publishing (no token needed)

### PyPI Configuration
1. Go to https://pypi.org/manage/project/esgcet/settings/publishing/
2. Add trusted publisher:
   - **Owner**: ESGF
   - **Repository**: esg-publisher
   - **Workflow**: publish-pypi.yml
   - **Environment**: (leave empty or use "release")

### ReadTheDocs Configuration
1. Import project from GitHub
2. Set default branch
3. Enable "Build pull requests" for preview
4. Configure versions to build (stable, latest, all tags)

## Migration Notes

### From Manual to Automated Releases

**Current Process** (assumed):
- Manual `python -m build`
- Manual `twine upload dist/*`
- Manual GitHub release creation

**New Process**:
- `git tag v5.5.0 && git push origin v5.5.0`
- Everything else automated

### Documentation Hosting

**Current**: Likely manual Sphinx builds or local hosting

**New**: Automated builds on readthedocs.org with:
- Multiple versions (stable, latest, per-version)
- Searchable documentation
- PDF/EPUB downloads
- SSL certificates
- CDN hosting

## Monitoring & Maintenance

### Workflow Health
- Monitor GitHub Actions tab for failures
- Set up notifications for failed workflows
- Review workflow runs monthly

### PyPI Package
- Monitor download statistics
- Check for security advisories
- Keep dependencies updated

### Documentation
- Check ReadTheDocs builds regularly
- Fix broken links
- Update outdated examples
- Add new sections as features develop

## Resources

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [ReadTheDocs Configuration](https://docs.readthedocs.io/en/stable/config-file/v2.html)
- [GitHub Actions Publishing](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
