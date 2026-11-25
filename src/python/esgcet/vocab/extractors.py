import cftime
import numpy as np
import xnetcdf

def get_geo(
        xnet_obj: xnetcdf.Dataset, 
        log, 
        lat_label: str = 'latitude',
        lon_label: str = 'longitude') -> None:
    """
    Obtain geo-spatial bounds from an xnetcdf object

    - north/east/south/west degrees
    - geo_units
    - height units/top/bottom
    - start/end datetime
    """
    geo_units = []

    # Check for axes
    if not hasattr(xnet_obj, 'dimensions'):
        log.warning("No axes extracted from data files")
        return

    record = {}

    axes = xnet_obj.variables
    if lat_label in axes:
        lat = xnet_obj[lat_label]

        geo_units.append(lat.attrs.get("units"))
        record["north_degrees"] = np.max(lat)
        record["south_degrees"] = np.min(lat)

    if lon_label in axes:
        lon = xnet_obj[lon_label]
        geo_units.append(lon.attrs["units"])
        record["east_degrees"] = np.max(lon)
        record["west_degrees"] = np.min(lon)

    if len(geo_units) > 0:
        record["geo_units"] = geo_units

    if "plev" in axes:
        plev = xnet_obj["plev"]
        record["height_units"]  = plev.attrs["units"]
        record["height_top"]    = np.max(plev)
        record["height_bottom"] = np.min(plev)

    # Extract temporal information
    if "time" not in axes:
        return record
    
    time   = xnet_obj["time"]
    time_units = time.attrs["units"]
    if not isinstance(time_units, str):
        log.warning(f'Unable to extract time info - unknown type "{time_units}"')
        return record

    if 'days since' not in time_units:
        log.warning(f'Unable to extract time info - unknown format "{time_units}"')
        return record
    
    if len(time_units.split()) < 3:
        log.error(f'Unable to extract time info - invalid format "{time_units}"')
        return record

    tu_start_inc = np.min(time)
    tu_end_inc   = np.max(time)

    dt_start = cftime.num2date(tu_start_inc, units=time_units, calendar=time.attrs.get('calendar','standard'))
    dt_end   = cftime.num2date(tu_end_inc,   units=time_units, calendar=time.attrs.get('calendar','standard'))

    record["datetime_start"] = dt_start
    record["datetime_end"] = dt_end

    return record