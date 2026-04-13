import typer

from . import kerchunk
from . import publisher
from . import qc_check 


app = typer.Typer(name="esgcet", no_args_is_help=True)

# Add subcommands from other modules
app.add_typer(kerchunk.app, name="kerchunk")
app.add_typer(publisher.app, name="publish")
app.add_typer(qc_check.app, name="qc-check")
