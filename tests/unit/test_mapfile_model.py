import pytest

from esgcet.kerchunk.mapfile_model import MapFileRecord


MAPFILE_RECORD = (
    "CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast.s2017-r1i1p1f1.Amon.psl.gn"
    "{separator}20210114 | "
    "$TEST_DATA/CMIP6/DCPP/MRI/MRI-ESM2-0/dcppA-hindcast/s2017-r1i1p1f1/"
    "Amon/psl/gn/v20210114/"
    "psl_Amon_MRI-ESM2-0_dcppA-hindcast_s2017-r1i1p1f1_gn_201711-202212.nc | "
    "5505592 | mod_time=1609786526.0 | "
    "checksum=1872faa5910eabb2bdc2cc756fd3bad34980d99ff7d2c1a35a5a3c1915339160 | "
    "checksum_type=SHA256"
)


@pytest.mark.parametrize("test_map_fixture", [
    "test_map_cmip6",
    pytest.param("test_map_cmip7", marks=pytest.mark.xfail(strict=True),),
])
def test_model_validator(request, test_map_fixture, esgvoc_available):
    if not esgvoc_available:
        pytest.skip("esgvoc not initialized - run 'esgvoc use cmip6@latest' first")

    test_map = request.getfixturevalue(test_map_fixture)

    with open(str(test_map), 'r') as fmap:
        for line in fmap:
            rec = MapFileRecord.model_validate(line)


@pytest.mark.parametrize("separator", ["#", ".v"])
def test_model_validator_supports_version_separators(data_dir, separator, esgvoc_available):
    if not esgvoc_available:
        pytest.skip("esgvoc not initialized - run 'esgvoc use cmip6@latest' first")

    line = MAPFILE_RECORD.format(separator=separator).replace("$TEST_DATA", str(data_dir))

    rec = MapFileRecord.model_validate(line)

    assert rec.dataset_id == (
        "CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast."
        "s2017-r1i1p1f1.Amon.psl.gn"
    )
    assert rec.version == 20210114
