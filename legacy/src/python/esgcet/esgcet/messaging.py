import logging

######################################################################
# Set the Python System Logging constants
######################################################################

debug = logging.getLogger('Debug').debug
info = logging.getLogger('Info').info
warning = logging.getLogger('Warning').warning
error = logging.getLogger('Error').error
critical = logging.getLogger('Critical').critical
exception = logging.getLogger('Exception').exception

