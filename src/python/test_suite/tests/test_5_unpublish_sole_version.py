import unittest

from tests import test_1_publish_d1v1

import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1

class Test5VerifyUnpublishSoleVersion(test_1_publish_d1v1.Test1VerifyPublishSingleDatasetSingleVersion):
    # All test numbers begin with 5

    def test_501_unpublish_from_solr_d1v1(self):
        self.tlog("Unpublishing from SOLR: %s" % ds1)
        publisher.unpublish_from_solr(ds1)

    def test_502_verify_unpublished_from_solr_d1v1(self):
        self.tlog("Verifying unpublished from SOLR: %s" % ds1)
        verify.verify_unpublished_from_solr(ds1)

    def test_503_unpublish_from_tds_d1v1(self):
        self.tlog("Unpublished from TDS: %s" % ds1)
        publisher.unpublish_from_tds(ds1)

    def test_504_verify_unpublished_from_tds_d1v1(self):
        self.tlog("Verifying unpublished from TDS: %s" % ds1)
        verify.verify_unpublished_from_tds(ds1)

    def test_505_unpublish_from_db_d1v1(self):
        self.tlog("Unpublished from db: %s" % ds1)
        publisher.unpublish_from_db(ds1)

    def test_506_verify_unpublished_from_db_d1v1(self):
        self.tlog("Verifying unpublished from db: %s" % ds1)
        verify.verify_unpublished_from_db(ds1)

    def test_507_verify_unpublished_d1v1(self):
        self.tlog("Verifying unpublished from all: %s" % ds1)
        verify.verify_dataset_unpublished(ds1)

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test5VerifyUnpublishSoleVersion)
    unittest.TextTestRunner(verbosity=2).run(suite)
