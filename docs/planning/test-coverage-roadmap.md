# Test Coverage Roadmap for esg-publisher

**Status**: Draft  
**Last Updated**: 2026-07-23  
**Version**: 5.5.0a (refactor branch)

## Current Coverage (46 tests)

- ✅ CLI commands (--help, --version) - 20 tests
- ✅ Backward compatibility (import paths) - 12 tests
- ✅ Project modules (GenericPublisher, ESGF15 Globus) - 3 tests
- ✅ Util modules (args, mapfile parsing) - 6 tests
- ✅ Kerchunk generation (with esgvoc) - 6 tests (2 kerchunk, 2 virtualizarr, 2 xfail)
- ⏭️ QAQC compliance checks - 4 tests (skipped, needs test files)

**Test execution time**: ~84s locally, ~113s in CI (Python 3.12)

## ~~Skipping (Being Phased Out)~~

- ~~Solr publishing/ingestion~~ - Legacy, being replaced by STAC
- ~~PID/citation connection methods~~ - Being phased out

## Priority 1: Core STAC Publishing (High Value, Medium Complexity)

### 1. STAC Converter (`src/python/esgcet/stac/stac_converter.py`)

**High Priority** - This is the current/future publishing path

**Test scenarios**:
- STAC catalog generation from mapfiles
- STAC item creation with correct metadata (temporal, spatial, etc.)
- Asset links (HTTP, Globus endpoints)
- Collection aggregation
- Error handling for malformed mapfiles

**Fixture needs**: 
- Sample mapfiles (CMIP6, CORDEX, input4MIPs)
- Expected STAC JSON outputs for validation ("golden files")
- Mock Globus endpoints

**Estimated**: 10-15 tests

### 2. STAC Client (`stac_client.py`)

**Test scenarios**:
- STAC catalog queries
- Filtering by project/version/variable
- Pagination handling

**Mock needs**: PySTAC-Client responses

**Estimated**: 5-8 tests

## Priority 2: Data Scanning & Validation (High Value, Low Complexity)

### 3. Scan Dataset (`src/python/esgcet/scan/scan_dataset.py`)

**Easy wins** - Pure file I/O, no external dependencies

**Test scenarios**:
- Recursive file discovery
- DRS path pattern matching
- File filtering (NetCDF only, exclude tmp/hidden files)
- Version detection from paths
- Handling missing directories
- Symlink handling

**Fixture needs**: 
- Mock directory tree with sample DRS structure
- Test NetCDF files (can be tiny/minimal - 1-2 variables)
- Edge cases: empty dirs, permission errors

**Estimated**: 8-10 tests

### 4. DRS Path Utilities (`src/python/esgcet/scan/`)

**Test scenarios**:
- DRS path parsing for different projects (CMIP6, CORDEX, etc.)
- Dataset ID generation from paths
- Version string extraction (vYYYYMMDD format)
- Invalid path handling

**Fixture needs**: Various DRS path examples per project

**Estimated**: 6-8 tests

## Priority 3: Update Operations (Medium Value, Medium Complexity)

### 5. Update Base (`update_base.py`, `update.py`)

**Test scenarios**:
- Version comparison (which is newer?)
- Incremental dataset updates
- File diff detection (new/removed/modified files)
- Checksum validation
- Handling partial updates

**Fixture needs**: 
- "Before" and "after" mapfile pairs
- Scenarios: add files, remove files, new version, replace files

**Estimated**: 10-12 tests

### 6. Update STAC (`update_stac.py`)

**Test scenarios**:
- STAC catalog updates (add/remove items)
- Metadata refresh
- Version tracking in STAC

**Mock needs**: Existing STAC catalog state

**Estimated**: 6-8 tests

## Priority 4: Globus Integration (Medium Value, Higher Complexity)

### 7. Globus Query (`globus_query.py`)

**Test scenarios**:
- Endpoint discovery
- Collection querying
- Filter construction
- Error handling (endpoint offline, auth failures)

**Mock needs**: Globus Search API responses

**Estimated**: 8-10 tests

### 8. ESGF15 Globus (`src/python/esgcet/esgf15/globus.py`)

**Already partially tested** - expand coverage

**Test scenarios**:
- Full indexing workflow
- Dataset/file record creation
- Error handling for missing endpoints
- Retry logic

**Estimated**: 5-7 additional tests

## Priority 5: Project-Specific Logic (Lower Priority)

### 9. Project Modules

Most DRS/metadata logic now in esgvoc, so these are lower priority.

**Modules**: `cmip6.py`, `input4mips.py`, `cordex.py`, etc.

**Test scenarios**:
- Project-specific overrides (if any)
- Custom validation rules
- Special handling for edge cases

**Estimated**: 4-6 tests per project (as needed)

## Implementation Plan

### **Phase 1** (Next PR - High ROI, Low Complexity)

**Focus**: Scan module - pure Python, no mocks needed

1. Create `tests/unit/test_scan_dataset.py`
2. Add fixture directory structure in `tests/unit/data/scan_fixtures/`
3. Test file discovery, DRS matching, version detection
4. Add minimal NetCDF test files

**Deliverable**: 8-10 new tests  
**Estimated effort**: ~2-3 hours  
**Coverage improvement**: ~10% (25% total)

### **Phase 2** (Following PR - High Value)

**Focus**: STAC converter - critical for current/future workflow

1. Create `tests/unit/test_stac_converter.py`
2. Add STAC output fixtures for validation (golden files)
3. Test catalog/item generation from mapfiles
4. Mock Globus endpoints where needed
5. Test error handling

**Deliverable**: 10-15 new tests  
**Estimated effort**: ~3-4 hours  
**Coverage improvement**: ~20% (45% total)

### **Phase 3** (Future Release)

**Focus**: Update operations and expanded Globus coverage

1. `tests/unit/test_update.py` - version comparison, diffs
2. `tests/unit/test_update_stac.py` - STAC refresh
3. Expand `test_esgf15_globus.py` coverage
4. `tests/unit/test_globus_query.py`

**Deliverable**: 15-20 new tests  
**Estimated effort**: ~4-5 hours  
**Coverage improvement**: ~20% (65% total)

### **Phase 4** (Nice to Have)

**Focus**: Integration tests and edge cases

1. End-to-end: scan → mapfile → STAC → publish
2. Error scenarios: missing files, bad metadata, network failures
3. Performance tests for large datasets
4. Concurrent operation tests

**Deliverable**: 10-15 integration tests  
**Estimated effort**: ~3-4 hours  
**Coverage improvement**: ~10% (75% total)

## Test Infrastructure To Add

### Phase 1 needs:
- ✅ Mock directory tree fixtures
- ✅ Tiny sample NetCDF files (1-2 variables, minimal data)
- ✅ DRS path examples for multiple projects

### Phase 2 needs:
- ⚠️ `pytest-mock` or `unittest.mock` patterns for HTTP requests
- ⚠️ Expected STAC JSON outputs (golden files)
- ⚠️ Mock Globus endpoint data
- ⚠️ Add `responses` library for HTTP mocking (optional dependency)

### Phase 3 needs:
- ⚠️ Mock PySTAC-Client responses
- ⚠️ Before/after dataset scenarios (versioning)
- ⚠️ Mock Globus SDK Transfer/Auth clients

### Phase 4 needs:
- ⚠️ Docker compose for local STAC server (integration tests)
- ⚠️ Performance benchmarking fixtures (large file lists)

## Coverage Goals

| Phase | Modules Tested | Coverage | Tests | Status |
|-------|---------------|----------|-------|--------|
| Current | 15% | 46 tests | - | ✅ Complete |
| Phase 1 | 25% | 54-56 tests | scan module | 📋 Planned |
| Phase 2 | 45% | 64-71 tests | STAC converter | 📋 Planned |
| Phase 3 | 65% | 79-91 tests | update + globus | 📋 Future |
| Phase 4 | 75% | 89-106 tests | integration | 📋 Future |

**Note**: Percentages exclude deprecated Solr/PID code.

## Next Immediate Step

**Recommendation**: Start with Phase 1 (scan module tests)

**Rationale**:
- Easiest to implement (no mocks, pure file I/O)
- High value (used in all publishing workflows)
- Good foundation for STAC tests (which consume scan results)
- Quick win to build momentum

**Action items**:
1. Create test file: `tests/unit/test_scan_dataset.py`
2. Add fixture data: `tests/unit/data/scan_fixtures/`
3. Generate minimal NetCDF samples
4. Write 8-10 tests covering file discovery and DRS matching
5. Run locally and via `act` to validate
6. Commit and push

## Dependencies

**Current test dependencies** (already in pyproject.toml):
```toml
[project.optional-dependencies]
dev = ["pytest>=9.0.0"]
```

**Recommended additions** for future phases:
```toml
dev = [
    "pytest>=9.0.0",
    "pytest-mock>=3.12.0",      # Phase 2: easier mocking
    "responses>=0.25.0",         # Phase 2: HTTP mocking for STAC
    "pytest-cov>=4.1.0",         # Coverage reporting
]
```

## CI/CD Integration

**Current**: GitHub Actions workflow runs tests on Python 3.11, 3.12, 3.13

**Future considerations**:
- Add coverage reporting (codecov or similar)
- Add pytest-xdist for parallel test execution (as suite grows)
- Add nightly builds for integration tests (if Docker needed)

## Notes

- All new tests should use existing fixtures (esgvoc, config) where applicable
- Maintain fast test execution (<2 minutes locally preferred)
- Mark slow tests with `@pytest.mark.slow` for optional skipping
- Keep mocks simple and maintainable - prefer fixture files over complex mock objects
