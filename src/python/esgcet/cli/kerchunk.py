
import typer

from pathlib import Path

from typing import Annotated, Literal

from esgcet.kerchunk.kerchunk_generator import KerchunkGenerator
from esgcet.kerchunk.mapfile_model import MapFileRecord, MapFileCatalog

from pydantic import AnyUrl, ValidationError

from dask.distributed import Client

import logging
from contextlib import nullcontext

app = typer.Typer(help=__doc__)

@app.command()
def generate(
    mapfile_path: Annotated[
        Path,
        typer.Argument(
            help = "the path of a map file or a directory with multiple map files"
        )
    ], 
    backend: Annotated[
        Literal["kerchunk", "virtualizarr"], 
        typer.Argument(
            help = "backend to generate kerchunk ref files"
        )
    ] = "kerchunk", 

    inline_threshold: Annotated[
        int,
        typer.Option(
            help = "only for kerchunk backend"
        )
    ] = 0,
    format: Annotated[
        Literal["json", "parquet"],
        typer.Option(
            help = "kerchunk ref file format"
        )
    ] = "json",

    source: Annotated[
        str,
        typer.Option(
            help = "source path to be replaced, not provided, then no replacement"
        )
    ] = None,

    target: Annotated[
        str,
        typer.Option(
            help = "target url to replace the source path, not provided, then no replacement"
        )
    ] = None,

    output_dir: Annotated[
        Path,
        typer.Option(
            help = "Output directory, default is the same directory of netcdf files"
        )
    ] = None,

    use_dask: Annotated[
        bool,
        typer.Option(
            help = "use dask to generate kerchunk, only valid for virtualizarr now"
        )
    ] = False,

    n_workers: Annotated[
        int,
        typer.Option(
            help = "dask worker number, only valid for virtualizarr now"
        )
    ] = 4,

) -> None:


    map_path = Path(mapfile_path)

    if map_path.is_file():
        if map_path.suffix != '.map':
            raise ValueError(f"File {map_path} is not a .map file")


        map_files = [map_path]

    elif map_path.is_dir():
        map_files = list(map_path.rglob("*.map"))
    else:
        raise ValueError(f"{map_path} does not exist")

    if not map_files:
        raise ValueError(f"cannot find valid map file under {map_path}")

    for map_file in map_files:
        if map_file.is_file():

            try:
                mf_cat = MapFileCatalog.from_mapfile(map_file)
                ncfiles = mf_cat.ncfiles

                if output_dir is None:
                    output_file = Path(mf_cat.records[0].file_path).parent / mf_cat.dataset_id + 'v' + str(mf_cat.version)
                else:
                    output_file = Path(output_dir) / Path(mf_cat.dataset_id + '.v' + str(mf_cat.version))

                generator = KerchunkGenerator(path_url = ncfiles, backend = backend, output_file = output_file, format = format)
                _run_generation(generator, source, target, inline_threshold, use_dask, n_workers)
            except ValidationError as e:
                print(f"validation failed for {map_file}: {e}")
            except TypeError as e:
                print(f"errors in kerchunk generation using {backend} for {map_file}: {e}")
            except Exception as e:
                print(f"unknown errors in kerchunk generation using {backend} for {map_file}: {e}")

def _run_generation(
    generator: KerchunkGenerator, 
    source: str, 
    target: str, 
    inline_threshold: int, 
    use_dask: bool,
    n_workers: int,
) -> None:

    ctx = (
        Client(
            n_workers=n_workers,
            threads_per_worker=1,
            processes=True,
            silence_logs=logging.ERROR,
        )
        if use_dask
        else nullcontext()
    )

    with ctx:
        generator.generate(source, target, inline_threshold, use_dask=use_dask)
