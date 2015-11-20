import unittest
import logging
import inspect
import sys

from utils import config
from utils.info_classes import PublicationLevels as pl
import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

ds1 = datasets.d1v1
ds2 = datasets.d1v2


class PublisherTests(unittest.TestCase):

    @classmethod
    def tlog(self, msg, log_level="info", show_method = False):
        if show_method:
            meth_name = inspect.stack()[1][0].f_code.co_name
            msg = "%s: %s" % (meth_name, msg)
        self.logger.log(getattr(logging, log_level.upper()), msg)

    @classmethod
    def setUpClass(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(getattr(logging, config.get("log_level")))
        stream_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(stream_handler)

        self.verify = verify.VerifyFuncs(self.logger)
        self.publisher = publisher.PublishFuncs(self.logger)

    @classmethod
    def tearDownClass(self):
        self.tlog("Removing all content after running tests.")
        self.ensure_empty()

    def ensure_empty(self):
        self.tlog("Verifying no test data published before we begin")
        try:
            self.verify.verify_empty_of_test_data()
            self.tlog("test data was already unpublished")
        except:
            self.tlog("some test data found - deleting all")
            self.publisher.delete_all()
            self.tlog("re-testing that no test data published")
            self.verify.verify_empty_of_test_data()

    def publish_and_verify(self, dsets):

        if not isinstance(dsets, list):
            dsets = [dsets]
        
        for ds in dsets:
            self.tlog("Publishing to db: %s" % ds.id)
            self.publisher.publish_to_db(ds)

        for ds in dsets:
            self.tlog("Verifying published to DB: %s" % ds.id)
            self.verify.verify_published(ds, [pl.db],
                                         db_suppress_file_url_checks = True)

        for ds in dsets:
            self.tlog("Publishing to TDS: %s" % ds.id)
            self.publisher.publish_to_tds(ds)

        for ds in dsets:
            self.tlog("Verifying published to TDS: %s" % ds.id)
            self.verify.verify_published(ds, [pl.tds])

        for ds in dsets:
            self.tlog("Publishing to SOLR: %s" % ds.id)
            self.publisher.publish_to_solr(ds)
        
        for ds in dsets:
            self.tlog("Verifying published to SOLR: %s" % ds.id)
            self.verify.verify_published(ds, [pl.solr])

        for ds in dsets:
            self.tlog("Verifying published to all: %s" % ds.id)
            self.verify.verify_published(ds)


    def verify_published(self, dsets):
        
        if not isinstance(dsets, list):
            dsets = [dsets]
        
        for ds in dsets:
            self.tlog("Verifying published to all: %s" % ds.id)
            self.verify.verify_published(ds)


    def unpublish_and_verify(self, dsets):

        if not isinstance(dsets, list):
            dsets = [dsets]
        
        for ds in dsets:
            self.tlog("Unpublishing from SOLR: %s" % ds.id)
            self.publisher.unpublish_from_solr(ds)

        for ds in dsets:
            self.tlog("Verifying unpublished from SOLR: %s" % ds.id)
            self.verify.verify_unpublished(ds, [pl.solr])

        for ds in dsets:
            self.tlog("Unpublished from TDS: %s" % ds.id)
            self.publisher.unpublish_from_tds(ds)

        for ds in dsets:
            self.tlog("Verifying unpublished from TDS: %s" % ds.id)
            self.verify.verify_unpublished(ds, [pl.tds])

        for ds in dsets:
            self.tlog("Unpublished from db: %s" % ds.id)
            self.publisher.unpublish_from_db(ds)

        for ds in dsets:
            self.tlog("Verifying unpublished from db: %s" % ds.id)
            self.verify.verify_unpublished(ds, [pl.db])

        for ds in dsets:
            self.tlog("Verifying unpublished from all: %s" % ds.id)
            self.verify.verify_unpublished(ds)

    def log_starting_test(self):
        st = inspect.stack()
        caller_name = st[1][3]
        self.tlog("\n\n=== starting %s ===\n" % caller_name)

    # separate test0 no longer needed - all tests start with call to ensure_empty()
    #def test_0_ensure_empty(self):
    #    self.log_starting_test()
    #    self.ensure_empty()

    def test_1_verify_publish_single_dataset_single_version(self):
        self.log_starting_test()
        self.ensure_empty()
        self.publish_and_verify(ds1)
        
    def test_2_verify_publish_single_dataset_two_versions(self):
        self.log_starting_test()
        self.ensure_empty()
        self.publish_and_verify(ds1)
        self.publish_and_verify(ds2)
        self.verify_published(ds1)
    
    def test_3_verify_publish_all_in_stages(self):
        self.log_starting_test()
        self.ensure_empty()
        self.publish_and_verify([ds1, ds2])
    
    def test_4_verify_publish_all_in_reverse(self):   
        self.log_starting_test()
        self.ensure_empty()
        self.publish_and_verify([ds2, ds1])
        
    def test_5_verify_unpublish_sole_version(self):
        self.log_starting_test()
        self.ensure_empty()
        self.publish_and_verify(ds1)
        self.unpublish_and_verify(ds1)

    def test_6_verify_unpublish_latest_of_multi_versions(self):
        self.log_starting_test()
        self.ensure_empty()
        self.publish_and_verify([ds1, ds2])
        self.unpublish_and_verify(ds2)
        self.verify_published(ds1)

    def test_7_verify_unpublish_earliest_of_multi_versions(self):
        self.log_starting_test()
        self.ensure_empty()
        self.publish_and_verify([ds1, ds2])
        self.unpublish_and_verify(ds1)
        self.verify_published(ds2)

    def test_8_parallel_publication(self):
        print "FIXME: implement parallel test"
        pass
