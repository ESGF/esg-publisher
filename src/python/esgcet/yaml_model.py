from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID

import types
from pathlib import Path
from typing import Any, get_args, get_origin, Literal, Union



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

    project: str

    globus_uuid: UUID | None = None
    index_node: str | None = None
    index_UUID: UUID | None = None
    globus_index: bool | None = False

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
    disable_qaqc: bool = False


# helpers

def is_optional(annotation: Any) -> bool:
    origin = get_origin(annotation)
    return (
        origin in (types.UnionType, Union)
        and type(None) in get_args(annotation)
    )


def unwrap_optional(annotation: Any) -> Any:
    return next(a for a in get_args(annotation) if a is not type(None))


def type_str(annotation: Any) -> str:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if is_optional(annotation):
        return type_str(unwrap_optional(annotation))

    if origin is Literal:
        return f"Literal[{', '.join(map(str, args))}]"

    if origin is list:
        inner = args[0] if args else Any
        return f"list[{type_str(inner)}]"

    if origin is dict:
        value = args[1] if len(args) > 1 else Any
        return f"dict[str, {type_str(value)}]"

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.__name__

    return getattr(annotation, "__name__", str(annotation))


def expand(annotation: Any):
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Optional[T]
    if is_optional(annotation):
        return expand(unwrap_optional(annotation))

    # list[T]
    if origin is list:
        inner = args[0] if args else Any
        return expand(inner)

    # dict[K,V] → ALWAYS example_key
    if origin is dict:
        value = args[1] if len(args) > 1 else Any
        return {
            "example_key": expand(value)
        }

    # BaseModel → recurse field-by-field
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        out = {}

        for name, field in annotation.model_fields.items():
            ann = field.annotation
            optional = is_optional(ann)

            base = f"{type_str(ann)}, {'optional' if optional else 'required'}"

            nested = expand(ann)   # RECURSION HAPPENS HERE

            if nested:
                out[name] = {
                    base: nested
                }
            else:
                out[name] = base

        return out

    return None


def model_to_template(model_cls: BaseModel) -> dict:
    out = {}

    for name, field in model_cls.model_fields.items():
        ann = field.annotation
        optional = is_optional(ann)

        base = f"{type_str(ann)}, {'optional' if optional else 'required'}"

        nested = expand(ann)   #  RECURSION ENTRY POINT

        if nested:
            out[f"{name}{{{base}}}"] = nested
        else:
            out[name] = base

    return out

def model_to_yaml(model_cls:BaseModel) -> dict:
    schema_dict = model_cls.model_json_schema()

    # Convert to YAML
    yaml_output = yaml.dump(schema_dict, default_flow_style=False)

    return yaml_output
