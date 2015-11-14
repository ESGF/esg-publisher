import unittest

from tests import test_0_verify_empty

import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1
ds2 = datasets.d1v2

class Test3VerifyPublishAllInStages(test_0_verify_empty.Test0VerifyEmpty):
    # All test numbers begin with 3

    all_datasets = (ds1, ds2)

    def test_301_verify_files_on_disk_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying files on disk: %s" % ds.id)
            verify.verify_files_on_disk(ds)
        
    def test_302_publish_to_db_all(self):
        for ds in self.all_datasets:
            self.tlog("Publishing to db: %s" % ds.id)
            publisher.publish_to_db(ds)

    def test_303_verify_published_to_db_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying files published to DB: %s" % ds.id)
            verify.verify_published_to_db(ds)

    def test_304_publish_to_tds_all(self):
        for ds in self.all_datasets:
            self.tlog("Publishing to TDS: %s" % ds.id)
            publisher.publish_to_tds(ds)

    def test_305_verify_published_to_tds_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying published to TDS: %s" % ds.id)
            verify.verify_published_to_tds(ds)

    def test_306_publish_to_tds_all(self):
        for ds in self.all_datasets:
            self.tlog("Publishing to SOLR: %s" % ds.id)
            publisher.publish_to_solr(ds)

    def test_307_verify_published_to_solr_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying published to SOLR: %s" % ds.id)
            verify.verify_published_to_solr(ds)

    def test_308_verify_published_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying published to all: %s" % ds.id)
            verify.verify_dataset_published(ds)

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test3VerifyPublishAllInStages)
    unittest.TextTestRunner(verbosity=2).run(suite)
