
import typer

from pathlib import Path

from typing import Annotated, Literal

from esgcet.kerchunk.kerchunk_generator import KerchunkGenerator
from esgcet.kerchunk.mapfile_model import MapFileRecord, MapFileCatalog

from pydantic import AnyUrl, ValidationError

from dask.distributed import Client

import logging
from contextlib import nullcontext
import yaml

app = typer.Typer(help=__doc__)

def load_config(config_path: Path) -> dict:
    """Load configuration file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.load(f, Loader=yaml.SafeLoader)
    except IOError:
        raise ValueError(f"Could not open config file: {config_path}")

def generate_dataset_id_from_path(path: Path, data_roots: dict) -> str:
    """
    Generate dataset-id from path using data_roots prefix mapping.

    Args:
        path: The directory path containing .nc files
        data_roots: Dictionary mapping filesystem prefixes to root names

    Returns:
        Generated dataset-id with path segments converted to dot notation
    """
    abs_path = path.resolve()

    # Find matching data_root prefix
    matched_prefix = None
    for prefix in data_roots.keys():
        prefix_path = Path(prefix).resolve()
        try:
            # Check if path is under this prefix
            abs_path.relative_to(prefix_path)
            matched_prefix = prefix_path
            break
        except ValueError:
            continue

    if matched_prefix is None:
        raise ValueError(
            f"Path {abs_path} does not match any data_roots prefix. "
            f"Available prefixes: {list(data_roots.keys())}"
        )

    # Get the relative path from the matched prefix
    rel_path = abs_path.relative_to(matched_prefix)

    # Convert path segments to dataset-id by replacing / with .
    dataset_id = str(rel_path).replace('/', '.')

    return dataset_id

@app.command()
def generate(
    mapfile_path: Annotated[
        Path,
        typer.Option(
            help = "the path of a map file or a directory with multiple map files"
        )
    ] = None,
    backend: Annotated[
        Literal["kerchunk", "virtualizarr"],
        typer.Option(
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

    path: Annotated[
        Path,
        typer.Option(
            help = "Path to a directory containing .nc files that are part of a multi-file dataset"
        )
    ] = None,

    dataset_id: Annotated[
        str,
        typer.Option(
            help = "Dataset ID to use when --path is provided (optional, will be auto-generated from path if not provided)"
        )
    ] = None,

    version: Annotated[
        str,
        typer.Option(
            help = "Version string to use when --path is provided (default: 'v1')"
        )
    ] = "v1",

    config: Annotated[
        Path,
        typer.Option(
            help = "Path to yaml config file (default: ~/.esg/esg.yaml)"
        )
    ] = None,

) -> None:


    if path is not None and mapfile_path is not None:
        raise ValueError("Cannot specify both --path and --mapfile_path. Use one or the other.")

    if path is None and mapfile_path is None:
        raise ValueError("Must specify either --path or mapfile_path")

    if path is not None:
        nc_path = Path(path)
        if not nc_path.is_dir():
            raise ValueError(f"Path {nc_path} is not a directory")

        ncfiles = sorted(list(nc_path.glob("*.nc")))
        ncfiles = [str(x) for x in ncfiles]
        if not ncfiles:
            raise ValueError(f"No .nc files found in {nc_path}")

        # Auto-generate dataset_id if not provided
        if not dataset_id:
            # Load config file
            if config is None:
                config_path = Path.home() / ".esg/esg.yaml"
            else:
                config_path = Path(config)

            if not config_path.exists():
                raise ValueError(
                    f"Config file not found at {config_path}. "
                    "Provide --config or --dataset-id when using --path"
                )

            cfg = load_config(config_path)
            data_roots = cfg.get('data_roots')
            if not data_roots:
                raise ValueError(
                    "data_roots not defined in config file. "
                    "Define data_roots in config or provide --dataset-id explicitly"
                )

            dataset_id = generate_dataset_id_from_path(nc_path, data_roots)
            print(f"Auto-generated dataset-id: {dataset_id}")

        if output_dir is None:
            output_file = nc_path / f"{dataset_id}.{version}"
        else:
            output_file = Path(output_dir) / f"{dataset_id}.{version}"

        try:
            generator = KerchunkGenerator(path_url=ncfiles, backend=backend, output_file=str(output_file), format=format)
            _run_generation(generator, source, target, inline_threshold, use_dask, n_workers)
        except ValidationError as e:
            print(f"validation failed: {e}")
        except TypeError as e:
            print(f"errors in kerchunk generation using {backend}: {e}")
        except Exception as e:
            print(f"unknown errors in kerchunk generation using {backend}: {e}")

    else:
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
