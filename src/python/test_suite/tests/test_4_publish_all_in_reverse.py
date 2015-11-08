import unittest

from tests import test_0_verify_empty

import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1
ds2 = datasets.d1v2

class Test4VerifyPublishAllInReverse(test_0_verify_empty.Test0VerifyEmpty):
    # All test numbers begin with 4

    all_datasets = (ds2, ds1)

    def test_301_put_files_on_disk_all(self):
        for ds in self.all_datasets:
            self.tlog("Putting files on disk: %s" % ds.id)
            publisher.put_files_on_disk(ds.id, ds.files)

    def test_302_verify_files_on_disk_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying files on disk: %s" % ds.id)
            verify.verify_files_on_disk(ds.id, ds.files)

    def test_303_publish_to_db_all(self):
        for ds in self.all_datasets:
            self.tlog("Publishing to db: %s" % ds.id)
            publisher.publish_to_db(ds.id, ds.files)

    def test_304_verify_published_to_db_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying files on disk: %s" % ds.id)
            verify.verify_published_to_db(ds.id, ds.files)

    def test_305_publish_to_tds_all(self):
        for ds in self.all_datasets:
            self.tlog("Publishing to TDS: %s" % ds.id)
            publisher.publish_to_tds(ds.id, ds.files)

    def test_306_verify_published_to_tds_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying published to TDS: %s" % ds.id)
            verify.verify_published_to_tds(ds.id, ds.files)

    def test_307_publish_to_tds_all(self):
        for ds in self.all_datasets:
            self.tlog("Publishing to SOLR: %s" % ds.id)
            publisher.publish_to_solr(ds.id, ds.files)

    def test_308_verify_published_to_solr_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying published to SOLR: %s" % ds.id)
            verify.verify_published_to_solr(ds.id, ds.files)

    def test_309_verify_published_all(self):
        for ds in self.all_datasets:
            self.tlog("Verifying published to all: %s" % ds.id)
            verify.verify_dataset_published(ds.id)

if __name__ == "__main__":

    suite = unittest.TestLoader().loadTestsFromTestCase(Test4VerifyPublishAllInReverse)
    unittest.TextTestRunner(verbosity=2).run(suite)
