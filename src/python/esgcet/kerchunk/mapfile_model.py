import pydantic
from typing import Literal, Iterable

from pydantic import (
    BaseModel,
    Field,
    model_validator,
    field_validator,
    model_serializer,
)

import esgvoc.api as ev
from esgvoc.apps.drs.validator import DrsValidator
from esgvoc.apps.drs.generator import DrsGenerator
from pathlib import Path
import re

import esgcet.logger as logger

log = logger.ESGPubLogger()

publog = log.return_logger(__name__)

#mapfile example:

# CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast.s2017-r1i1p1f1.Amon.psl.gn#20210114 | $TEST_DATA/CMIP6/DCPP/MRI/MRI-ESM2-0/dcppA-hindcast/s2017-r1i1p1f1/Amon/psl/gn/v20210114/psl_Amon_MRI-ESM2-0_dcppA-hindcast_s2017-r1i1p1f1_gn_201711-202212.nc | 5505592 | mo
# d_time=1609786526.0 | checksum=1872faa5910eabb2bdc2cc756fd3bad34980d99ff7d2c1a35a5a3c1915339160 | checksum_type=SHA256

# CMIP6.CMIP.MOHC.UKESM1-0-LL.piControl.r1i1p1f2.fx.areacella.gn.v20190705 | /nl/themis/esgf/cli137/world-shared/globus/css03_data/CMIP6/CMIP/MOHC/UKESM1-0-LL/piControl/r1i1p1f2/fx/areacella/gn/v20190705/areacella_fx_UKESM1-0-LL_piControl_r1i1p1f2_gn.nc
#| 65542 | mod_time=1562646491.0 | checksum=f49cfaa297b2ac074517100599db62343b2bc41d106ae22d7f3553259fea598e

class MapFileRecord(BaseModel):
    dataset_id: str
    version: int
    file_path: str
    size: int
    mod_time: float
    checksum: str
    checksum_type: Literal["SHA256"] | None
    project: Literal["CMIP6", "CMIP6Plus", "CMIP7"] = Field(..., exclude=True)



    @field_validator("checksum")
    @classmethod
    def validate_checksum(cls, v):
        if not re.fullmatch(r"[a-f0-9]{64}", v):
            raise ValueError("Invalid SHA256 checksum")
        return v

    @model_validator(mode="before")
    @classmethod
    def parse_record(
        cls,
        value: str,
    ) -> dict[str, str|int|float]:

        if isinstance(value, str):
            parts = [p.strip() for p in value.split("|")]

            if parts[0].split('.')[0] in ["CMIP6", "CMIP6Plus", "CMIP7"]:
                project = parts[0].split('.')[0]
            elif parts[0].split('.')[1] in ["CMIP6", "CMIP6Plus", "CMIP7"]:
                project = parts[0].split('.')[1]

            else:
                raise ValueError(f"Invalid record format {parts[0]}")

            cls._validator = DrsValidator(project_id=project.lower())
            cls._generator = DrsGenerator(project_id=project.lower())


            if "CMIP6" in project and len(parts) < 6:
                raise ValueError("Invalid record format")

            elif len(parts) < 5:
                raise ValueError(f"Invalid record format for {project}")

            if "CMIP6" in project:
                dataset_id, version_str = parts[0].split('#')
            else:

                try:
                    last_v_index = parts[0].rfind('v')
                    dataset_id = parts[0][:last_v_index-1]
                    version_str = parts[0][last_v_index+1:]
                except:
                    raise ValueError("the dataset_id is invalid")

            version = int(version_str)
            file_path = parts[1]
            size = int(parts[2])

            mod_time = float(parts[3].split("=")[1])
            checksum = parts[4].split("=")[1]
            if "CMIP6" in project:
                checksum_type = parts[5].split("=")[1]
            else:
                checksum_type = None

            return dict(
                dataset_id=dataset_id,
                version=version,
                file_path=file_path,
                size=size,
                mod_time=mod_time,
                checksum=checksum,
                checksum_type=checksum_type,
                project=project
            )
        return value

    @model_validator(mode="after")
    def validate_dataset_id_path(self):
        """
        Validate dataset id and path using esgvoc.
        """

        validator = DrsValidator(project_id=self.project.lower())
        # esgvoc provides dataset id validation against vocabularies

        if not validator.validate_dataset_id(drs_expression=self.dataset_id).validated:
            raise ValueError(f"Invalid {self.project} dataset_id: {self.dataset_id}")


        v_path = Path(self.file_path)
        parts = v_path.parts
        try:
            cmip_index = parts.index(self.project)
            result = "/".join(parts[cmip_index:-1])  # Includes everything after CMIP6/7/plus
        except ValueError as err:
            raise ValueError(f"{self.project} not found in path") from err

        vd_dr_result = validator.validate_directory(drs_expression=result)

        vd_fn_result = validator.validate_file_name(drs_expression=v_path.name)

        if not vd_dr_result.validated or not vd_fn_result.validated:
            raise ValueError(f"File path does not look like a {self.project} path")
        return self


    @model_validator(mode="after")
    def check_consistency(self):
        """
        Cross-check dataset_id and file_path.
        """
        generator = DrsGenerator(project_id=self.project.lower())


        v_path = Path(self.file_path)
        parts = v_path.parts
        try:
            cmip_index = parts.index(self.project)
        except ValueError as err:
            raise ValueError(f"{self.project} not found in path") from err
        m_bag = list(parts[cmip_index:])

        if self.dataset_id.split(".") == generator.generate_dataset_id_from_bag_of_terms(m_bag):
            raise ValueError("dataset_id not consistent with file_path")

        return self


    def to_catalog_line(self) -> str:

        if "CMIP6" in self.project:
            return " | ".join(
                [
                    self.dataset_id + "#" + str(self.version),
                    self.file_path,
                    str(self.size),
                    f"mod_time={self.mod_time}",
                    f"checksum={self.checksum}",
                    f"checksum_type={self.checksum_type}",
                ]
            )
        else:
            return " | ".join(
                [
                    self.dataset_id + ".v" + str(self.version),
                    self.file_path,
                    str(self.size),
                    f"mod_time={self.mod_time}",
                    f"checksum={self.checksum}",
                ]
            )

    @model_serializer
    def serialize(self):
        return self.to_catalog_line()

    @classmethod
    def serialize_catalog(cls, records: Iterable["MapFileRecord"], outfile: str):
        """
        Serialize a collection of records to a CMIP catalog file.
        """
        with open(outfile, "w") as f:
            for rec in records:
                f.write(rec.model_dump() + "\n")


class MapFileCatalog(BaseModel):
    records: list[MapFileRecord]

    @model_validator(mode="after")
    def validate_single_dataset(self):
        """
        Ensure all records belong to the same dataset_id.
        """
        dataset_ids = {r.dataset_id for r in self.records}

        if len(dataset_ids) != 1:
            raise ValueError(
                f"Multiple dataset_ids detected: {dataset_ids}"
            )

        return self

    @property
    def dataset_id(self):
        return self.records[0].dataset_id

    @property
    def ncfiles(self):
        return [rec.file_path for rec in self.records]

    @property
    def version(self):
        return self.records[0].version

    def serialize_catalog(self, outfile: str):
        with open(outfile, "w") as f:
            for r in self.records:
                f.write(r.model_dump() + "\n")

    @classmethod
    def from_mapfile(cls, map_file: str| Path) -> "MapFileCatalog":
        records = []
        with open(map_file, "r") as fmap:
            for line in fmap:
                rec = MapFileRecord.model_validate(line)
                records.append(rec)

        return cls(records=records)
