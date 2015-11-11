import unittest

from tests import test_0_verify_empty

import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1

class Test1VerifyPublishSingleDatasetSingleVersion(test_0_verify_empty.Test0VerifyEmpty):
    # All test numbers begin with 1

    def test_101_verify_files_on_disk_d1v1(self):
        self.tlog("Verifying files on disk: %s" % ds1.id)
        verify.verify_files_on_disk(ds1.id, ds1.files)

    def test_102_publish_to_db_d1v1(self):
        self.tlog("Publishing to db: %s" % ds1.id)
        publisher.publish_to_db(ds1.id, ds1.files)

    def test_103_verify_published_to_db_d1v1(self):
        self.tlog("Verifying published to DB: %s" % ds1.id)
        verify.verify_published_to_db(ds1.id, ds1.files)

    def test_104_publish_to_tds_d1v1(self):
        self.tlog("Publishing to TDS: %s" % ds1.id)
        publisher.publish_to_tds(ds1.id, ds1.files)

    def test_105_verify_published_to_tds_d1v1(self):
        self.tlog("Verifying published to TDS: %s" % ds1.id)
        verify.verify_published_to_tds(ds1.id, ds1.files)

    def test_106_publish_to_tds_d1v1(self):
        self.tlog("Publishing to SOLR: %s" % ds1.id)
        publisher.publish_to_solr(ds1.id, ds1.files)

    def test_107_verify_published_to_solr_d1v1(self):
        self.tlog("Verifying published to SOLR: %s" % ds1.id)
        verify.verify_published_to_solr(ds1.id, ds1.files)

    def test_108_verify_published_d1v1(self):
        self.tlog("Verifying published to all: %s" % ds1.id)
        verify.verify_dataset_published(ds1.id)

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test1VerifyPublishSingleDatasetSingleVersion)
    unittest.TextTestRunner(verbosity=2).run(suite)
