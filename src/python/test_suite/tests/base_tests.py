import unittest
import logging
import inspect

from utils import config

logging.basicConfig()

import utils.wrap_esgf_publisher as publisher

class PublishBaseTest(unittest.TestCase):

    @classmethod
    def tlog(self, msg, log_level="info"):
        meth_name = inspect.stack()[1][0].f_code.co_name
        self.log.log(getattr(logging, log_level.upper()), "%s: %s" % (meth_name, msg))

    @classmethod
    def setUpClass(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(getattr(logging, config.get("log_level")))
        self.tlog("Setting up...", "INFO")
        publisher.delete_all()

    @classmethod
    def tearDownClass(self):
        publisher.delete_all()
        self.log.info("Removing all content after running tests.")

if __name__ == "__main__":

    unittest.main()
