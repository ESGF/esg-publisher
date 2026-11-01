"""Fast, metadata-only NetCDF4 dataset scanning.

The xarray handler opens every file as one logical dataset. That can construct a
large Dask graph and spend minutes inspecting a publication. This handler opens
each mapped file independently and reads only attributes and coordinates.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import netCDF4
import numpy as np

from esgcet.scan.handler_base import ESGPubHandlerBase


@dataclass
class NC4ScanResult:
    """Small, in-memory result consumed by ``ESGPubMakeDataset``."""

    attrs: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, dict[str, Any]] = field(default_factory=dict)
    files: dict[str, dict[str, Any]] = field(default_factory=dict)
    north_degrees: float | None = None
    south_degrees: float | None = None
    east_degrees: float | None = None
    west_degrees: float | None = None
    datetime_start: str | None = None
    datetime_end: str | None = None
    height_top: Any = None
    height_bottom: Any = None
    height_units: str | None = None
    geo_units: list[str] = field(default_factory=list)


class ESGPubNC4Handler(ESGPubHandlerBase):
    """Extract dataset metadata without loading dataset data variables."""

    @staticmethod
    def _to_python(value: Any) -> Any:
        """Return JSON-serializable Python values for NetCDF/NumPy objects."""

        if np.ma.isMaskedArray(value):
            if value.ndim == 0:
                return None if bool(value.mask) else value.item()
            return [
                ESGPubNC4Handler._to_python(item)
                for item in value.tolist(fill_value=None)
            ]
        if np.ma.is_masked(value):
            return None
        if isinstance(value, np.ndarray):
            return [ESGPubNC4Handler._to_python(item) for item in value.tolist()]
        if isinstance(value, np.generic):
            return ESGPubNC4Handler._to_python(value.item())
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, tuple):
            return [ESGPubNC4Handler._to_python(item) for item in value]
        if isinstance(value, list):
            return [ESGPubNC4Handler._to_python(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): ESGPubNC4Handler._to_python(item)
                for key, item in value.items()
            }
        return value

    @classmethod
    def _attrs(cls, obj: Any) -> dict[str, Any]:
        return {
            name: cls._to_python(obj.getncattr(name))
            for name in obj.ncattrs()
        }

    @staticmethod
    def _mapped_paths(map_data: list[list[Any]]) -> list[str]:
        """Return unique file paths in mapfile order."""

        paths: list[str] = []
        seen: set[str] = set()
        for record in map_data:
            path = str(record[1])
            if path not in seen:
                paths.append(path)
                seen.add(path)
        return paths

    @staticmethod
    def _coordinate(dataset: netCDF4.Dataset, *names: str):
        for name in names:
            if name in dataset.variables:
                return dataset.variables[name]
        return None

    @staticmethod
    def _extrema(variable: netCDF4.Variable) -> tuple[float, float] | None:
        values = variable[:]
        if np.ma.isMaskedArray(values):
            values = values.compressed()
        else:
            values = np.asarray(values).reshape(-1)
        if values.size == 0:
            return None
        return float(np.min(values)), float(np.max(values))

    @classmethod
    def _datetime_string(cls, value: Any) -> str:
        value = cls._to_python(value)
        if hasattr(value, "isoformat"):
            result = value.isoformat(timespec="seconds")
            return result if result.endswith("Z") else result + "Z"
        return str(value)

    @classmethod
    def _time_endpoints(cls, variable: netCDF4.Variable) -> tuple[str, str] | None:
        if variable.size == 0:
            return None

        first_value = variable[0]
        last_value = variable[-1]
        units = getattr(variable, "units", None)
        if units:
            calendar = getattr(variable, "calendar", "standard")
            first_value = netCDF4.num2date(
                first_value, units=units, calendar=calendar
            )
            last_value = netCDF4.num2date(
                last_value, units=units, calendar=calendar
            )
        return cls._datetime_string(first_value), cls._datetime_string(last_value)

    @classmethod
    def nc4_load(cls, map_data: list[list[Any]]) -> NC4ScanResult:
        """Scan mapped files without constructing a multi-file data array."""

        paths = cls._mapped_paths(map_data)
        if not paths:
            raise RuntimeError("No files found in map data")

        result = NC4ScanResult()
        time_starts: list[str] = []
        time_ends: list[str] = []

        for index, filename in enumerate(paths):
            path = Path(filename)
            if not path.is_file():
                raise FileNotFoundError(f"Mapped NetCDF file not found: {filename}")

            with netCDF4.Dataset(path) as dataset:
                if index == 0:
                    result.attrs = cls._attrs(dataset)

                # Match xarray's publisher-facing variables mapping. Attributes
                # are sufficient; no data variable values are read.
                for name, variable in dataset.variables.items():
                    result.variables.setdefault(name, cls._attrs(variable))

                file_record: dict[str, Any] = {}
                if "tracking_id" in dataset.ncattrs():
                    file_record["tracking_id"] = cls._to_python(
                        dataset.getncattr("tracking_id")
                    )
                result.files[filename] = file_record

                latitude = cls._coordinate(dataset, "lat", "latitude")
                if latitude is not None:
                    extrema = cls._extrema(latitude)
                    if extrema is not None:
                        south, north = extrema
                        result.south_degrees = (
                            south if result.south_degrees is None
                            else min(result.south_degrees, south)
                        )
                        result.north_degrees = (
                            north if result.north_degrees is None
                            else max(result.north_degrees, north)
                        )
                    cls._add_geo_units(result, latitude)

                longitude = cls._coordinate(dataset, "lon", "longitude")
                if longitude is not None:
                    extrema = cls._extrema(longitude)
                    if extrema is not None:
                        west, east = extrema
                        result.west_degrees = (
                            west if result.west_degrees is None
                            else min(result.west_degrees, west)
                        )
                        result.east_degrees = (
                            east if result.east_degrees is None
                            else max(result.east_degrees, east)
                        )
                    cls._add_geo_units(result, longitude)

                time = cls._coordinate(dataset, "time")
                if time is not None:
                    endpoints = cls._time_endpoints(time)
                    if endpoints is not None:
                        start, end = endpoints
                        time_starts.append(start)
                        time_ends.append(end)

                pressure = cls._coordinate(dataset, "plev")
                if pressure is not None and pressure.size:
                    values = pressure[:]
                    if np.ma.isMaskedArray(values):
                        values = values.compressed()
                    else:
                        values = np.asarray(values).reshape(-1)
                    if values.size:
                        result.height_top = cls._to_python(values[0])
                        result.height_bottom = cls._to_python(values[-1])
                        units = getattr(pressure, "units", None)
                        if units:
                            result.height_units = str(cls._to_python(units))

        # ISO timestamps sort chronologically for supported publication dates.
        if time_starts:
            result.datetime_start = min(time_starts)
            result.datetime_end = max(time_ends)

        return result

    @classmethod
    def _add_geo_units(
        cls, result: NC4ScanResult, variable: netCDF4.Variable
    ) -> None:
        units = getattr(variable, "units", None)
        if units:
            units = str(cls._to_python(units))
            if units not in result.geo_units:
                result.geo_units.append(units)

    def get_attrs_dict(self, scanobj: NC4ScanResult) -> dict[str, Any]:
        return scanobj.attrs

    def get_scanfile_dict(
        self,
        scandata: NC4ScanResult,
        mapdata: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        records: dict[str, dict[str, Any]] = {}
        for record in mapdata:
            filename = record["file"]
            file_metadata = scandata.files.get(filename, {})
            if "tracking_id" not in file_metadata:
                self.publog.warning("Tracking ID not found in %s", filename)
            records[filename] = file_metadata
        return records

    def get_variables(
        self, scanobj: NC4ScanResult
    ) -> dict[str, dict[str, Any]]:
        return scanobj.variables

    def get_variable_list(
        self, variables: dict[str, dict[str, Any]]
    ) -> list[str]:
        return list(variables)

    def set_bounds(self, record: dict[str, Any], scanobj: NC4ScanResult) -> None:
        for name in (
            "north_degrees", "south_degrees", "east_degrees", "west_degrees",
            "datetime_start", "datetime_end", "height_top", "height_bottom",
        ):
            value = getattr(scanobj, name)
            if value is not None:
                record[name] = value

        if scanobj.height_units is not None:
            record["height_units"] = scanobj.height_units
        if scanobj.geo_units:
            record["geo_units"] = scanobj.geo_units
