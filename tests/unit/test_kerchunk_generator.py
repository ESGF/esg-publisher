import pytest


from esgcet.kerchunk.kerchunk_generator import KerchunkGenerator
from esgcet.kerchunk.mapfile_model import MapFileRecord, MapFileCatalog
from pathlib import Path
import json
import xarray as xr
import fsspec



@pytest.mark.parametrize(
    "backend, inline_threshold", [
        ("kerchunk", 0),
        pytest.param("kerchunk", 500, marks=pytest.mark.xfail(strict=True),),
        ("virtualizarr",0),
    ]
)
def test_kerychunk_generator_cmip6(data_dir, test_map_cmip6, tmp_path, backend, inline_threshold, esgvoc_available):
    if not esgvoc_available:
        pytest.skip("esgvoc not initialized - run 'esgvoc use cmip6@latest' first")

    records = []
    with open(str(test_map_cmip6), 'r') as fmap:
        for line in fmap:

            new_line = line.replace("$TEST_DATA", str(data_dir))
            rec = MapFileRecord.model_validate(new_line)
            records.append(rec)


    mf_cat = MapFileCatalog(records=records) 

    expected_file = data_dir / f"kerchunk/{mf_cat.dataset_id}.v{mf_cat.version}.json.{backend}"
    output_file = tmp_path / "test.json"
    

    generator = KerchunkGenerator(path_url=mf_cat.ncfiles, backend=backend, output_file=output_file, format="json")

    #old_url = "/autofs/nccsopen-svm1_home/mfx/MyGit/esg-publisher/tests/unit/data/"
    old_uri = str(data_dir)
    new_uri = "https://esgf-node.ornl.gov/thredds/fileServer/"

    generator.generate(old_uri, new_uri, inline_threshold)


    actual = json.loads(output_file.read_text())
    expected = json.loads(Path(expected_file).read_text())

    assert actual == expected
