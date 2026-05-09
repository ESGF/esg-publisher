from pydantic import BaseModel, Field
from uuid import UUID

from pathlib import Path


class PIDCred(BaseModel):
    password: str | None = None
    port: int = 5671
    priority: int = 1
    ssl_enabled: bool = True
    user: str
    vhost: str


class UserProjectConfigEntry(BaseModel):
    CONST_ATTR: dict[str, str]
    pid_prefix: str | None = None
    DRS: list[str] | None = None

class StacClient(BaseModel):
    client_id: UUID
    redirect_uri: HttpUrl

class StacTransactionAPI(BaseModel):
    client_id: UUID
    access_control_policy: HttpUrl
    scope_string: str
    base_url: HttpUrl

class StacConfig(BaseModel):
    stac_client: StacClient
    token_storage_file: Path
    stac_transaction_api: StacTransactionAPI
    stac_api: HttpUrl
    disable_qaqc: bool = False

class KerchunkConfig(BaseModel):
    data_dir: Path
    new_uri: str
    old_uri: str
    backend: Literal["kechunk", "virtualizarr"]
    format: Literal["json", "parquet"]
    inline_threshold: int


class Config(BaseModel):
    cmip6_clone: str | None= None
    cmor_path: str | None = None

    data_node: str | None = None
    data_roots: dict[str, str] | None = None

    globus_uuid: UUID | None = None
    index_node: str | None = None

    pid_creds: dict[str, PIDCred] | None = None

    set_replica: bool = False
    silent: bool = False
    verbose: bool = False
    skip_prepare: bool = True
    test: bool = False

    user_project_config: dict[str, UserProjectConfigEntry] | None = None

    non_netcdf: bool = False
    disable_citation: bool = True
    disable_further_info: bool = True

    https_url: str | None = None
    skip_opendap: bool = False

    stac_config: StacConfig | None
    kerchunk_config: KerchunkConfig | None
