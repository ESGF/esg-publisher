import unittest
import utils.verify as verify
from tests.base_tests import PublishBaseTest

class Test0VerifyEmpty(PublishBaseTest):

    def test_001_verify_empty_of_test_data(self):
        self.tlog("Verifying no test data published before we begin")
        verify.verify_empty_of_test_data()

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test0VerifyEmpty)
    unittest.TextTestRunner(verbosity=2).run(suite)
