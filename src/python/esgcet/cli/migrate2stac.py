import typer
from esgcet.esgf15.migrate_esgf15_stac import migrate_serial as esgf_migrate_serial
from esgcet.esgf15.migrate_esgf15_stac import migrate_dask as esgf_migrate_dask

from esgcet.esgf15.globus import Project
from typing import Literal

import duckdb
from duckdb import DuckDBPyConnection
from esgcet.esgf15.process_kerchunk import ProcessLog
import pathlib

app = typer.Typer()


def _validate_project(project: str) -> Project:
    if project is not None:
        for p in Project:
            if p.value == project:
                return p

        raise typer.BadParameter(f"project: {project} not supported")


@app.command()
def esgf15(
    institution_id: str = typer.Argument(help="institution id"),
    data_node: Literal["anl", "ornl", "nersc"] = typer.Argument(help="data node name"),
    project: str = typer.Argument(help="project name", callback=_validate_project),
    dataset_file: str = typer.Option(help="path to the dataset file including the dataset id", default=None),
    is_replica: bool | None= typer.Option(help="is replica?", default=None),
    dataset_limit: int = typer.Option(help="dataset limit for each batch query", default=1000),
    config_file: str | None = typer.Option(
        help="config yaml file path, default will read the esg.yaml under $HOME/.config/esg_publisher"
    ),
    total: int | None = typer.Option(help="total number of published document for test purpose", default=None),
    init_marker: str | None = typer.Option(
        help="the global scroll marker from the previous query",
        default=None
    ),
    drs_method: Literal["drs", "simple"] | None = typer.Option(
        help="the directory struncture for the kerchunk files: drs/simple",
        default="drs"
    ),
    n_workers: int = typer.Option(
        help="number of dask worker, 0 mean serial",
        default=0
    ),
) -> None:
    """Migrate ESGF1.5 or solr metadata to stac"""

    # provenance
    csv_filename = f"{project.value}_{institution_id}_{data_node}_{drs_method}.csv"
    con_log = ProcessLog(csv_filename)

    if pathlib.Path(dataset_file).exists():
        dataset_file = str(pathlib.Path(dataset_file).resolve())
        print(
            f"Dataset will be read from: {dataset_file}. \n"
            f"{project}, {data_node} {institution_id} just used to verify the datasets"
        )
    else:
        dataset_file = None
        print ("Normal Query")

    if n_workers <= 0:
        esgf_migrate_serial(
            institution_id = institution_id,
            data_node = data_node,
            project = project,
            dataset_file = dataset_file,
            is_replica = is_replica,
            dataset_limit = dataset_limit,
            config_file = config_file,
            total = total,
            init_marker = init_marker,
            method = drs_method,
            con_log = con_log,
        )


    else:
        esgf_migrate_dask(
            institution_id = institution_id,
            data_node = data_node,
            project = project,
            dataset_file = dataset_file,
            is_replica = is_replica,
            dataset_limit = dataset_limit,
            config_file = config_file,
            total = total,
            init_marker = init_marker,
            method = drs_method,
            con_log = con_log,
            n_workers=n_workers,
        )


    con_log.log_update()
    con_log.con.close()

    pass

@app.command()
def solr() -> None:
    pass
