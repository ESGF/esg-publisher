import typer

from . import kerchunk_gen
from . import publisher


app = typer.Typer(name="esgcet", no_args_is_help=True)

# Add subcommands from other modules
app.add_typer(kerchunk_gen.app, name="kerchunk-gen")
app.add_typer(publisher.app, name="publish")
