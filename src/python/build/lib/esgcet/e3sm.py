from esgcet.generic_netcdf import GenericPublisher
import sys


class e3sm(GenericPublisher):

    def __init__(self, argdict):
        super().__init__(argdict)
        self.project = "e3sm" 