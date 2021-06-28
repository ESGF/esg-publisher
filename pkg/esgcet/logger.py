import logging


class Logger:

    def __init__(self):
        pass

    def return_logger(self, name):
        publog = logging.getLogger(name)
        publog.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        publog.addHandler(handler)
        return publog
