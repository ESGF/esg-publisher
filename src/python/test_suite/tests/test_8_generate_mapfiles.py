import unittest

from tests import test_0_verify_empty

import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1

class Test8VerifyGenerateMapfiles(test_0_verify_empty.Test0VerifyEmpty):
    # All test numbers begin with 8

    # WHAT SHOULD WE DO HERE?
    pass

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test8VerifyGenerateMapfiles)
    unittest.TextTestRunner(verbosity=2).run(suite)
