from pydantic import BaseModel, AnyUrl, model_validator
from typing import Literal, Any
from pathlib import Path
import json, re
from kerchunk.combine import MultiZarrToZarr
from kerchunk.df import refs_to_dataframe
from kerchunk.hdf import SingleHdf5ToZarr
from kerchunk.netCDF3 import NetCDF3ToZarr
from typing import Literal
import virtualizarr as vz
from virtualizarr import open_virtual_mfdataset
from virtualizarr.parsers import HDFParser
from obstore.store import LocalStore, from_url
from obspec_utils.registry import ObjectStoreRegistry
import tempfile
from urllib.parse import urljoin
import warnings

class KerchunkGenerator(BaseModel):
    "Kerchunk generation for ESGF"

    path_url: str | AnyUrl | list[str] | list[AnyUrl] 
    backend: str = Literal['kerchunk', 'virtualizarr']
    output_file: str | Path | None
    format: str = Literal["json", "parquet"]


    files: list[str | Path] = None


    @model_validator(mode="after")
    def validate_path_url(self) -> "KerchunkGenerator":
        if not isinstance(self.path_url, list):
            self.files = [self.path_url]
        else:
            self.files = self.path_url

        return self

    @staticmethod
    def build_ref(fn: str, out_dir: Path, inline_threshold: int) -> str:
        out_path = Path(out_dir) / Path(Path(fn).name).with_suffix(".json")
        try:
            h5chunks = SingleHdf5ToZarr(fn, inline_threshold=inline_threshold)
        except Exception as e:
            try:
                h5chunks = NetCDF3ToZarr(fn, inline_threshold=inline_threshold)
            except Exception as e2:
                raise ValueError(f"Cannot read file {fn}: \n {e} \n {e2}")
        with open(out_path, "w") as f:
            json.dump(h5chunks.translate(), f)
        return out_path

    @staticmethod
    def combine(*,
        ref_dir: str | Path,
        ref_format: Literal['json', 'parquet'],
    ) -> None:
        """combine mutiple reference files in a dataset to a single file."""
    
        refs = Path(ref_dir) if isinstance(ref_dir, str) else ref_dir
    
        json_list = []
        for jsn in refs.glob(f"*.json"):
            json_list.append(jsn)
    
        if len(json_list) > 1:
            mzz = MultiZarrToZarr(
                json_list,
                concat_dims=["time"],
                #identical_dims=["lat", "lon"],
            )
            combined = mzz.translate()
        else:
            with open(json_list[0], 'r') as f:
                 combined = json.load(f)

        return combined


    @staticmethod
    def rename_target_prefix(*,
        refs: dict[str, Any],
        renames: dict[str, str]
    ) -> dict[str, Any]:
        """rename the target from local filesystem to https url."""

        out = {}
        for k, v in refs["refs"].items():
            if isinstance(v, list) and isinstance(v[0], str):
                for old, new in renames.items():
                    if v[0].startswith(old.rstrip("/")):
                        v[0] = v[0].replace(old.rstrip("/"), new.rstrip("/"))
            out[k] = v
        refs["refs"] = out
        return refs

    @staticmethod
    def serialize(
        refs: dict[str, Any],
        formater: Literal['parquet', 'json'],
        filename: str,
    ) -> None:
        """serialize the reference data."""

        file_path = Path(filename) 

        if formater == 'parquet':
            refs_to_dataframe(refs, 
                file_path if file_path == ".parq" else file_path.with_suffix(".parq")
            )
        else:
            with open(
                file_path if file_path == ".json" else file_path.with_suffix(".json"),
                "w"
            ) as fjson:
                json.dump(refs, fjson)
    
        return None

    @staticmethod
    def create_http_url(new_http_url: str) -> str:
        """a wrapper to input the new_http_url to the callback functions of vz's rename_paths."""
        def local_to_http_url(
            old_local_path: str | Path,
        ) -> str:
            """return a https url from a file path."""
            from pathlib import Path

            #new_http_url = "https://esgf-node.ornl.gov/thredds/fileServer/css03_data/CMIP6/CMIP/E3SM-Project/E3SM-2-1/1pctCO2/r1i1p1f1/Amon/cli/gr/v20240206/"

            filename = Path(old_local_path).name

            return urljoin(new_http_url,str(filename))
        return local_to_http_url


    def generate(
        self, 
        old_uri: str | AnyUrl,
        new_uri: str | AnyUrl,
        inline_threshold: int=0,
        use_dask: bool = False,
    ) -> None:

        if self.backend == "kerchunk":
            self.kerchunk_backend(old_uri, new_uri, inline_threshold)
        else:
            self.virtualizarr_backend(old_uri, new_uri, use_dask)

    def virtualizarr_backend(
        self,
        old_uri: str | AnyUrl | Path,
        new_uri: str | AnyUrl | Path,
        use_dask: bool = False,
    ) -> None:

        warnings.filterwarnings(
            "ignore",
            message="Numcodecs codecs are not in the Zarr version 3 specification*",
            category=UserWarning
        )

        parser = HDFParser()

        file_path = Path(self.files[0]).parent
        file_url = f"file://{file_path}"
        store = LocalStore(prefix=old_uri)
        registry = ObjectStoreRegistry({file_url: store})

        # Build virtual dataset
        vds = vz.open_virtual_mfdataset(
            self.files,
            combine="nested",
            concat_dim="time",
            parser=parser,
            registry=registry,
            parallel='dask' if use_dask else False,
            coords='minimal',
            compat='override',
        )

        if old_uri and new_uri:
            base_path = file_path.relative_to(Path(old_uri))
            http_url = urljoin(new_uri.rstrip("/")+"/", str(base_path).rstrip("/") + "/")
            meta = vds.vz.rename_paths(self.create_http_url(http_url))
        else:
            meta = vds
        # Convert to kerchunk reference dictionary
        refs = meta.vz.to_kerchunk()

        self.serialize(refs, self.format, self.output_file)

        # save to different formats

        return None

    def kerchunk_backend(
        self,
        old_uri: str | AnyUrl | Path,
        new_uri: str | AnyUrl | Path,
        inline_threshold: int,
    ) -> None:

        with tempfile.TemporaryDirectory() as tmpdir:

            for f in self.files:
                self.build_ref(f, tmpdir, inline_threshold)

            combined = self.combine(ref_dir=tmpdir, ref_format="json")
            if old_uri and new_uri:
                replaced_ref = self.rename_target_prefix(refs = combined, renames = {old_uri: new_uri})
            else:
                replaced_ref = combined
            self.serialize(replaced_ref, self.format, self.output_file)
