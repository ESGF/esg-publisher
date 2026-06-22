import typer
from esgcet.esgf15.migrate_esgf15_stac import migrate as esgf_migrate

from esgcet.esgf15.globus import Project
from typing import Literal

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
    dataset_limit: int = typer.Option(help="dataset limit for each batch query", default=1000),
    config_file: str | None = typer.Option(
        help="config yaml file path, default will read the esg.yaml under $HOME/.config/esg_publisher"
    ),
    total: int | None = typer.Option(help="total number of published document for test purpose", default=None),
) -> None:
    """Migrate ESGF1.5 or solr metadata to stac"""

    esgf_migrate(
        institution_id = institution_id,
        data_node = data_node, 
        project = project,
        dataset_limit = dataset_limit,
        config_file = config_file,
        total = total,
    )


    pass

@app.command()
def solr() -> None:
    pass
