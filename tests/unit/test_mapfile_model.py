import pytest

from esgcet.kerchunk.mapfile_model import MapFileRecord


@pytest.mark.parametrize("test_map_fixture", [
    "test_map_cmip6",
    pytest.param("test_map_cmip7", marks=pytest.mark.xfail(strict=True),),
])
def test_model_validator(request, test_map_fixture):

    test_map = request.getfixturevalue(test_map_fixture)

    with open(str(test_map), 'r') as fmap:
        for line in fmap:
            rec = MapFileRecord.model_validate(line)
