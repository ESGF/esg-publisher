import unittest

from tests import test_2_publish_d1v2

import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1
ds2 = datasets.d1v2

class Test6VerifyUnpublishLatestOfMultiVersions(test_2_publish_d1v2.Test2VerifyPublishSingleDatasetTwoVersions):
    # All test numbers begin with 6

    def test_601_unpublish_from_solr_d1v2(self):
        self.tlog("Unpublishing from SOLR: %s" % ds2.id)
        publisher.unpublish_from_solr(ds2.id, ds2.files)

    def test_602_verify_unpublished_from_solr_d1v2(self):
        self.tlog("Verifying unpublished from SOLR: %s" % ds2.id)
        verify.verify_unpublished_from_solr(ds2.id, ds2.files)

    def test_603_verify_published_d1v1(self):
        self.tlog("Verifying published to all: %s" % ds1.id)
        verify.verify_dataset_published(ds1.id)

    def test_604_unpublish_from_tds_d1v2(self):
        self.tlog("Unpublished from TDS: %s" % ds2.id)
        publisher.unpublish_from_tds(ds2.id, ds2.files)

    def test_605_verify_unpublished_from_tds_d1v2(self):
        self.tlog("Verifying unpublished from TDS: %s" % ds2.id)
        verify.verify_unpublished_from_tds(ds2.id, ds2.files)

    def test_606_verify_published_d1v1(self):
        self.tlog("Verifying published to all: %s" % ds1.id)
        verify.verify_dataset_published(ds1.id)

    def test_607_unpublish_from_db_d1v2(self):
        self.tlog("Unpublished from db: %s" % ds2.id)
        publisher.unpublish_from_db(ds2.id, ds2.files)

    def test_608_verify_unpublished_from_db_d1v2(self):
        self.tlog("Verifying unpublished from db: %s" % ds2.id)
        verify.verify_unpublished_from_db(ds2.id, ds2.files)

    def test_609_verify_published_d1v1(self):
        self.tlog("Verifying published to all: %s" % ds1.id)
        verify.verify_dataset_published(ds1.id)

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test6VerifyUnpublishLatestOfMultiVersions)
    unittest.TextTestRunner(verbosity=2).run(suite)
