import unittest

from tests import test_1_publish_d1v1

import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1
ds2 = datasets.d1v2

class Test2VerifyPublishSingleDatasetTwoVersions(test_1_publish_d1v1.Test1VerifyPublishSingleDatasetSingleVersion):
    # All test numbers begin with 1

    def test_201_publish_to_db_d1v2(self):
        self.tlog("Publishing to db: %s" % ds2.id)
        publisher.publish_to_db(ds2)

    def test_202_verify_published_to_db_d1v2(self):
        self.tlog("Verifying files published to DB: %s" % ds2.id)
        verify.verify_published_to_db(ds2)

    def test_203_publish_to_tds_d1v2(self):
        self.tlog("Publishing to TDS: %s" % ds2.id)
        publisher.publish_to_tds(ds2)

    def test_204_verify_published_to_tds_d1v2(self):
        self.tlog("Verifying published to TDS: %s" % ds2.id)
        verify.verify_published_to_tds(ds2)

    def test_205_publish_to_tds_d1v2(self):
        self.tlog("Publishing to SOLR: %s" % ds2.id)
        publisher.publish_to_solr(ds2)

    def test_206_verify_published_to_solr_d1v2(self):
        self.tlog("Verifying published to SOLR: %s" % ds2.id)
        verify.verify_published_to_solr(ds2)

    def test_207_verify_published_d1v2(self):
        self.tlog("Verifying published to all: %s" % ds2.id)
        verify.verify_dataset_published(ds2)   

    def test_208_verify_published_to_db_d1v1(self):
        self.tlog("Verifying published to DB: %s" % ds1.id)
        verify.verify_published_to_db(ds1)

    def test_209_verify_published_to_tds_d1v1(self):
        self.tlog("Verifying published to TDS: %s" % ds1.id)
        verify.verify_published_to_tds(ds1)

    def test_210_verify_published_to_solr_d1v1(self):
        self.tlog("Verifying published to SOLR: %s" % ds1.id)
        verify.verify_published_to_solr(ds1)

    def test_211_verify_published_d1v1(self):
        self.tlog("Verifying published to all: %s" % ds1.id)
        verify.verify_dataset_published(ds1)

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test2VerifyPublishSingleDatasetTwoVersions)
    unittest.TextTestRunner(verbosity=2).run(suite)
