from thredds import readThreddsWithAuthentication
from esgcet.config import getConfig
from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning, error, critical, exception

def reinitializeLAS():
    """
    Reinitialize the Live Access Server. This forces the catalogs to be reread.

    Returns the HTML string returned from the URL.

    """
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")

    lasReinitUrl = config.get('DEFAULT', 'las_reinit_url')
    info("Reinitializing LAS server")

    try:
        reinitResult = readThreddsWithAuthentication(lasReinitUrl, config)
    except Exception, e:
        raise ESGPublishError("Error reinitializing the Live Access Server: %s"%e)
        
    return reinitResult
