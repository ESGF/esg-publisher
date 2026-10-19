import yaml
from collections import deque
from pydantic import validate_call, ConfigDict
from typing import Any, Literal, Generator
from pathlib import Path
from platformdirs import PlatformDirs
from duckdb import DuckDBPyConnection

from esgcet.util import logger
from esgcet.esgf15.globus import ESGFGlobusIndex, Project
from esgcet.esgf15.process_kerchunk import (
    KerchunkResult,
    ProcessLog,
    generate_kerchunk_for_entry,
    process_publish_result,
)
from esgcet.esgf15.data_node_config import DATA_NODE_MAPPING

from esgcet.stac.stac_converter import ESGSTACConverter, ESGSTACItem
from esgcet.stac.stac_client import (
    getTransactionClient,
    GlobusTransactionClient,
    EGITransactionClient,
)

from dask.distributed import Client, LocalCluster, Future, as_completed


log = logger.ESGPubLogger()
publog = log.return_logger(__name__)


def _esgf15_index_generator(
    *,
    institution_id: str,
    data_node: Literal["anl", "ornl", "nersc"],
    project: Project,
    init_marker: str | None = None,
    dataset_file: str | None = None,
    is_replica: bool | None= False,
    dataset_limit: int = 1000,
) -> tuple[
    ESGFGlobusIndex, Generator[list[list[dict[str, Any]]], None, None]
]:

    esgf15_index = ESGFGlobusIndex(init_marker=init_marker)
    esgf15_generator = esgf15_index.query_dataset_file(
        project = project,
        fixed_facet = {
            "institution_id": institution_id,
            "latest": True,
            "retracted": False,
        },
        data_node = DATA_NODE_MAPPING[data_node],
        dataset_file = dataset_file,
        is_replica = is_replica,
        dataset_limit = dataset_limit,
    )
    return esgf15_index, esgf15_generator

@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def migrate_serial(*,
    institution_id: str,
    data_node: Literal["anl", "ornl", "nersc"],
    project: Project,
    dataset_file: str | None = None,
    is_replica: bool | None= False,
    dataset_limit: int = 1000,
    config_file: Path | None,
    total: int | None = None,
    init_marker: str | None = None,
    method: Literal["drs", "simple"] = "drs",
    con_log: ProcessLog | None = None,
) -> None:
    """migrate esgf1.5 cmip6 records to stac collections/items and
       plubish them to stac catalog"""

    config = _pre_setting_config(dataset_limit, config_file)

    esgf15_index, esgf15_generator = _esgf15_index_generator(
         institution_id = institution_id,
         data_node = data_node,
         project = project,
         init_marker = init_marker,
         dataset_file = dataset_file,
         is_replica = is_replica,
         dataset_limit = dataset_limit,
    )

    esgf_stac_convert = ESGSTACConverter(config.get('stac_config'))
    TransactionClient = getTransactionClient(config.get("stac_config"))

    argdict = {
        "verbose": False,
        "dry_run": False,
        "save_stac": False,
        "silent": False,
        "stac_config": config.get('stac_config'),
    }
    tc = TransactionClient(argdict)
    if not tc:
        raise RuntimeError("Failed to create STAC transaction client")

    no_published = 0
    no_processed = 0
    for record in esgf15_generator:
        for entry in record:

            stac_submission = 0
            dataset_id = entry[0].get("id", "<unknown>")
            kc_result = generate_kerchunk_for_entry(
                entry,
                dataset_id,
                config,
                project.value,
                method,
            )

            kc_result.marker = esgf15_index.marker
            kc_result.next_marker = esgf15_index.next_marker

            no_processed += 1
            no_published += process_publish_result(
                kc_result,
                config,
                con_log.con,
                data_node,
                esgf_stac_convert,
                tc,
            )
            if no_processed % 200 == 0:
                con_log.log_update()

            if total and no_processed >= total:
                return
        esgf15_index.marker = esgf15_index.next_marker


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def migrate_dask(*,
    institution_id: str,
    data_node: Literal["anl", "ornl", "nersc"],
    project: Project,
    dataset_file: str | None = None,
    is_replica: bool | None= False,
    dataset_limit: int = 1000,
    config_file: Path | None,
    total: int | None = None,
    init_marker: str | None = None,
    method: Literal["drs", "simple"] = "drs",
    con_log: ProcessLog | None = None,
    n_workers: int,
) -> None:
    """migrate esgf1.5 cmip6 records to stac collections/items and
       plubish them to stac catalog"""

    config = _pre_setting_config(dataset_limit, config_file)

    esgf15_index, esgf15_generator = _esgf15_index_generator(
         institution_id = institution_id,
         data_node = data_node,
         project = project,
         init_marker = init_marker,
         dataset_file = dataset_file,
         is_replica = is_replica,
         dataset_limit = dataset_limit,
    )

    """Process ESGF datasets with Dask.

    Kerchunk generation runs on Dask workers.
    STAC publishing and DuckDB logging remain serial.
    """

    esgf_stac_convert = ESGSTACConverter(config.get('stac_config'))
    TransactionClient = getTransactionClient(config.get("stac_config"))

    argdict = {
        "verbose": False,
        "dry_run": False,
        "save_stac": False,
        "silent": False,
        "stac_config": config.get('stac_config'),
    }
    tc = TransactionClient(argdict)
    if not tc:
        raise RuntimeError("Failed to create STAC transaction client")




    no_published = 0
    no_processed = 0
    exhausted = False


    pending: dict[
        Future[KerchunkResult],
        tuple[str, str | None, str | None],
    ] = {}

    # Entries waiting to be submitted.
    entry_queue: deque[
        tuple[list[dict[str, Any]], str | None, str | None]
    ] = deque()

    with LocalCluster(
        n_workers=n_workers,
        threads_per_worker=1,
    ) as cluster:
        with Client(cluster) as client:

            futures = as_completed()
            scheduler_workers = len(client.scheduler_info()["workers"])
            max_workers = max(1, 1 * scheduler_workers)
            def submit_entry(
                entry: list[dict[str,Any]],
                marker: str | None,
                next_marker: str | None,
            ) -> None:
                dataset_id = entry[0].get("id", "<unknown>")

                future = client.submit(
                    generate_kerchunk_for_entry,
                    entry,
                    dataset_id,
                    config,
                    project.value,
                    method,
                    pure=False,
                )

                futures.add(future)

                pending[future] = (
                    dataset_id,
                    marker,
                    next_marker,
                )

            def fill_queue() -> None:
                """Fill Dask with up to max_workers tasks."""

                nonlocal exhausted
                while (
                    len(pending) < max_workers
                    and not exhausted
                ):
                    # First use entries already obtained from a record.
                    if entry_queue:
                        entry, marker, next_marker = entry_queue.pop()

                        submit_entry(
                            entry,
                            marker,
                            next_marker,
                        )
                        continue
                    # Otherwise get the next ESGF record.
                    try:
                        record = next(esgf15_generator)
                    except StopIteration:
                        exhausted = True
                        break

                    marker = esgf15_index.marker
                    next_marker = esgf15_index.next_marker

                    for entry in record:
                        entry_queue.append(
                            (
                                entry,
                                marker,
                                next_marker,
                            )
                        )

            # Initial submission.
            fill_queue()
            while pending:
                future = next(futures)
                dataset_id, marker, next_marker = pending.pop(
                    future
                )
                try:
                    result = future.result()
                except Exception as ex:
                    publog.error(
                        f"Unexpected Dask failure for {dataset_id} due to {ex}",
                    )
                    result = KerchunkResult(
                        dataset_id=dataset_id,
                        success=False,
                        error_msg=(
                            f"Unexpected Dask worker failure: {ex}"
                        ),
                    )
                result.marker = marker
                result.next_marker = next_marker

                publog.info(f"marker: {marker}, next_marker: {next_marker}")

                no_published += process_publish_result(
                    result=result,
                    config=config,
                    con=con_log.con,
                    data_node=data_node,
                    esgf_stac_convert=esgf_stac_convert,
                    tc=tc,
                )

                no_processed += 1
                if no_processed % 200 == 0:
                    con_log.log_update()

                if (
                    total is not None
                    and no_published >= total
                ):
                    break
                # A task completed, so submit more work.
                fill_queue()


            if (
                total is not None
                and no_published >= total
            ):
                for future in pending:
                    future.cancel()

    return None

def _pre_setting_config(
    dataset_limit: int,
    config_file: Path | None,
) -> dict[str, Any]:

    if dataset_limit > 2000:
        raise ValueError(
            "suggested vaule is < 2000, if not, "
            "the next globus post search may exceed its maximum 10000!!!"
        )

    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

    else:
        platform_dirs = PlatformDirs("esg_publisher", "ESGF2-US")

        alt_config_file = Path(platform_dirs.user_config_dir) / "esg.yaml"
        if alt_config_file.exists():

            publog.info("use the config file in the system directory")
            with open(alt_config_file, 'r') as file:
                config = yaml.safe_load(file)
        else:
            raise ValueError("Please provide valid config file")

    if 'stac_config' not in config:
        raise ValueError("please provide stac_config in the config file")
    else:
        if not config.get('stac_config').get('stac_api', None):
            raise ValueError("stac_api is missing")

    return config
