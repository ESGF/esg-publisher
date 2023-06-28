import logging


class ESGPubLogger:
    """
    Logger wrapper class
    """
    def __init__(self):
        """ Constructor
        """
        pass

    def return_logger(self, name, silent=False, verbose=False):
        """
        Logger 'factory' method allows for the naming and level specification.
        """
        publog = logging.getLogger(name)
        if silent:
            publog.setLevel(logging.WARNING)
        elif verbose:
            publog.setLevel(logging.DEBUG)
        else:
            publog.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        publog.addHandler(handler)
        return publog
