import typer
from esgcet.esgf15.migrate_esgf15_stac import migrate as esgf_migrate

from esgcet.esgf15.globus import Project
from typing import Literal

import duckdb
from duckdb import DuckDBPyConnection

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
    is_replica: bool = typer.Option(help="is replica?", default=False),
    dataset_limit: int = typer.Option(help="dataset limit for each batch query", default=1000),
    config_file: str | None = typer.Option(
        help="config yaml file path, default will read the esg.yaml under $HOME/.config/esg_publisher"
    ),
    total: int | None = typer.Option(help="total number of published document for test purpose", default=None),
    init_marker: str | None = typer.Option(
        help="the global scroll marker from the previous query",
        default=None
    ),
    drs_method: str | None = typer.Option(
        help="the directory struncture for the kerchunk files: drs/simple",
        default="drs"
    ),
) -> None:
    """Migrate ESGF1.5 or solr metadata to stac"""

    # provenance
    con = process_and_log()

    esgf_migrate(
        institution_id = institution_id,
        data_node = data_node, 
        project = project,
        is_replica = is_replica,
        dataset_limit = dataset_limit,
        config_file = config_file,
        total = total,
        init_marker = init_marker,
        method = drs_method,
        con = con,
    )

    csv_filename = f"{project.value}_{institution_id}_{data_node}_{drs_method}.csv"

    con.execute(f"COPY log_table TO '{csv_filename}' (HEADER, DELIMITER ',')")

    pass

@app.command()
def solr() -> None:
    pass


def process_and_log() -> DuckDBPyConnection:
    con = duckdb.connect(database=':memory:')
    con.execute("""
        CREATE TABLE log_table (
            timestamp TIMESTAMP,
            dataset_id VARCHAR,
            marker VARCHAR,
            next_marker VARCHAR,
            kerchunk_file VARCHAR,
            stac_submission INTEGER,
            message VARCHAR
        )
    """)

    return con
