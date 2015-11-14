import unittest

from tests import test_2_publish_d1v2

import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1
ds2 = datasets.d1v2

class Test7VerifyUnpublishEarliestOfMultiVersions(test_2_publish_d1v2.Test2VerifyPublishSingleDatasetTwoVersions):
    # All test numbers begin with 7

    def test_701_unpublish_from_solr_d1v1(self):
        self.tlog("Unpublishing from SOLR: %s" % ds1.id)
        publisher.unpublish_from_solr(ds1)

    def test_702_verify_unpublished_from_solr_d1v1(self):
        self.tlog("Verifying unpublished from SOLR: %s" % ds1.id)
        verify.verify_unpublished_from_solr(ds1)

    def test_703_verify_published_d1v2(self):
        self.tlog("Verifying published to all: %s" % ds2.id)
        verify.verify_dataset_published(ds2)

    def test_704_unpublish_from_tds_d1v1(self):
        self.tlog("Unpublished from TDS: %s" % ds1.id)
        publisher.unpublish_from_tds(ds1)

    def test_705_verify_unpublished_from_tds_d1v1(self):
        self.tlog("Verifying unpublished from TDS: %s" % ds1.id)
        verify.verify_unpublished_from_tds(ds1)

    def test_706_verify_published_d1v2(self):
        self.tlog("Verifying published to all: %s" % ds2.id)
        verify.verify_dataset_published(ds2)

    def test_707_unpublish_from_db_d1v1(self):
        self.tlog("Unpublished from db: %s" % ds1.id)
        publisher.unpublish_from_db(ds1)

    def test_708_verify_unpublished_from_db_d1v1(self):
        self.tlog("Verifying unpublished from db: %s" % ds1.id)
        verify.verify_unpublished_from_db(ds1)

    def test_709_verify_published_d1v2(self):
        self.tlog("Verifying published to all: %s" % ds2.id)
        verify.verify_dataset_published(ds2)

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test7VerifyUnpublishEarliestOfMultiVersions)
    unittest.TextTestRunner(verbosity=2).run(suite)
