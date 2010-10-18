#!/usr/bin/env python

from cmip5_tables import cmor_variables, requested_time

def getProduct(cmor_table, variable, experiment, year1, year2):
    """Get the DRS product value associated with the file.
    Returns
      'output1' for datasets to be replicated,
      'output2' for datasets outside the replicated datasets,
      'output' if the product cannot be determined.
    """
    cmor_table = cmor_table.lower()
    variable = variable.lower()

    # decadal1960, decadal1980, decadal2005 => decadal_30
    # Other decadal experiments => decadal_10
    if experiment[0:7]=='decadal':
        if experiment in ['decadal1960', 'decadal1980', 'decadal2005']:
            experiment = 'decadal_30'
        else:
            experiment = 'decadal_10'

    # If the variable is not in the request list, => output2
    vardict = cmor_variables.get(cmor_table, None)
    reqdict = requested_time.get(cmor_table, None)

    # If the CMOR table or variable are unknown, don't even try
    if vardict is None or variable is None:
        result = 'output'

    # Check for variables outside the request list
    elif variable not in vardict:
        result = 'output2'

    # CMOR table == 'day'
    elif cmor_table == 'day':
        if variable in ['huss', 'omldamax', 'pr', 'psl', 'sfcwind', 'tas', 'tasmax', 'tasmin', 'tos', 'tossq']:
            result = 'output1'
        else:
            result = getTimeDependentProduct(cmor_table, variable, experiment, reqdict, year1, year2)

    # CMOR table == 'Oyr'
    elif cmor_table == 'oyr':
        priority, dimensions = vardict[variable]
        if priority in [1,2]:
            result = 'output1'
        else:
            result = 'output2'

    # CMOR table == 'Omon'
    elif cmor_table == 'omon':
        priority, dimensions = vardict[variable]
        if 'basin' in dimensions:
            result = 'output1'
        elif 'olevel' in dimensions:
            result = 'output2'
        else:
            result = 'output1'

    # CMOR table == 'aero'
    elif cmor_table == 'aero':
        priority, dimensions = vardict[variable]
        if 'alev' not in dimensions:
            result = 'output1'
        else:
            result = getTimeDependentProduct(cmor_table, variable, experiment, reqdict, year1, year2)

    # CMOR table == '6hrPlev', '3hr', 'cfMon', 'cfOff'
    elif cmor_table in ['6hrplev', '3hr', 'cfmon', 'cfoff']:
        result = getTimeDependentProduct(cmor_table, variable, experiment, reqdict, year1, year2)

    # Otherwise => output1
    else:
        result = 'output1'

    return result

def getTimeDependentProduct(cmor_table, variable, experiment, reqdict, year1, year2):
    if experiment not in reqdict:
        result = 'output1'
    elif (year1 is None) and (year2 is None):
        result = 'output'
    else:
        reqspec = reqdict[experiment]

        # Absolute time range
        if reqspec[0]=='abs':
            result = 'output2'
            for y1, y2 in reqspec[1]:
                if y1<=year1<=year2 and y1<=year2<=y2:
                    result = 'output1'
                    break

        # Not an absolute time range: punt for now
        else:
            result = 'output'

    return result
