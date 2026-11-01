import typer

from . import kerchunk
from . import publisher
from . import qc_check 
from . import migrate2stac


app = typer.Typer(name="esgcet", no_args_is_help=True)

# Add subcommands from other modules
app.add_typer(kerchunk.app, name="kerchunk")
app.add_typer(qc_check.app, name="qc-check")
app.add_typer(migrate2stac.app, name="migrate2stac")

app.add_typer(
    kerchunk.app,
    name="kerchunk",
    help="Generate Kerchunks from a map file or a directory with multiple map files.",
)

app.add_typer(
    qc_check.app,
    name="qc-check",
    help="Run quality-control checks on datasets.",
)

app.add_typer(
    migrate2stac.app,
    name="migrate2stac",
    help="Migrate ESGF1.5 metadata to STAC.",
)
