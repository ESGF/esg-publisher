import typer


app = typer.Typer(help=__doc__)

@app.command()
def publish() -> None:
    pass


