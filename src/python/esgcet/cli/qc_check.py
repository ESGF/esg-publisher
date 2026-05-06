import typer

from compliance_checker.runner import CheckSuite, ComplianceChecker

from esgcet.kerchunk.mapfile_model import MapFileRecord, MapFileCatalog

from typing import Annotated, Literal

from pathlib import Path
from esgcet.settings import QAQC

app = typer.Typer(help=__doc__)

@app.command()
def cc(
    mapfile_path: Annotated[
        Path,
        typer.Argument(
            help = "the path of a map file or a directory with multiple map files"
        )
    ],
    project: Annotated[
        Literal["CMIP6", "CMIP6Plus", "CMIP7"],
        typer.Argument(
            help = "project name"
        )
    ],
    criteria: Annotated[
        Literal["lenient", "normal", "strict"] | None,
        typer.Option("--criteria", "-c", help="criteria, will overide the values in setting")
    ] = None,

    skip_checks: Annotated[
        list[str] | None,
        typer.Option("--skip-checks", "-s", help="skip checks, will overide the values in setting")
    ] = None,

    include_checks: Annotated[
        list[str] | None,
        typer.Option("--include-checks", "-i", help="include checks, will overide the values in setting")
    ] = None,

    verbose: Annotated[
        Literal[0,1,2],
        typer.Option("--verbose", help="verbose")
    ] = 0,

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

    check_suite = CheckSuite()
    check_suite.load_all_available_checkers()
    project_qc_config = QAQC.get(project.lower(), None)

    for map_file in map_files:
        if map_file.is_file():
            try:
                mf_cat = MapFileCatalog.from_mapfile(map_file)
                ccreport_file = Path(map_file).with_suffix(".ccreport").name

                return_value, errors = ComplianceChecker.run_checker(
                    mf_cat.ncfiles,
                    project_qc_config['test'],
                    verbose,
                    criteria if criteria else project_qc_config['criteria'],
                    skip_checks if skip_checks else project_qc_config['skip_checks'], # skip_checks
                    include_checks if include_checks else project_qc_config['include_checks'], # include
                    ccreport_file,  # outputfilename
                    ["text"]
                )
                if errors:
                    print(f"Checker Errors {errors}")
                    raise RuntimeError(f"Errors from compliance checker {errors}")

            except Exception as e:
                print (f"something is wrong: {e}")



    pass


