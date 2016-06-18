import unittest
import logging
import inspect
import sys
import time

from utils import config
from utils.info_classes import PublicationLevels as pl
import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

from utils.parallel_procs import PoolWrapper

ds1 = datasets.d1v1
ds2 = datasets.d1v2



class PublisherTests(unittest.TestCase):

    @classmethod
    def tlog(cls, msg, log_level="info", show_method = False):
        if show_method:
            meth_name = inspect.stack()[1][0].f_code.co_name
            msg = "%s: %s" % (meth_name, msg)
        cls.logger.log(getattr(logging, log_level.upper()), msg)

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(cls.__class__.__name__)
        cls.logger.setLevel(getattr(logging, config.get("log_level")))
        stream_handler = logging.StreamHandler(sys.stdout)
        cls.logger.addHandler(stream_handler)

        cls.verify = verify.VerifyFuncs(cls.logger)
        cls.publisher = publisher.PublishFuncs(cls.logger)

    @classmethod
    def tearDownClass(cls):
        cls.tlog("Removing all content after running tests.")
        cls.ensure_empty()

    @classmethod
    def ensure_empty(cls, dset_list=None):
        """
        Verify that no test data is already published. By default, it will use 
        datasets.all_datasets as the list, but the list of datasets to check
        can be passed in instead.
        """
        cls.tlog("Verifying no test data published before we begin")
        try:
            cls.verify.verify_empty_of_test_data(dset_list=dset_list)
            cls.tlog("test data was already unpublished")
        except:
            cls.tlog("some test data found - deleting all")
            cls.publisher.delete_all(dset_list=dset_list)
            cls.tlog("re-testing that no test data published")
            # when testing, allow SOLR time to update
            cls.verify.verify_empty_of_test_data(solr_retry=True)

    def publish_and_verify(self, dsets):

        if not isinstance(dsets, list):
            dsets = [dsets]
        
        for ds in dsets:
            self.publish_single_db(ds)
        for ds in dsets:
            self.verify_published_single_db(ds)
        for ds in dsets:
            self.publish_single_tds(ds)
        for ds in dsets:
            self.verify_published_single_tds(ds)
        for ds in dsets:
            self.publish_single_solr(ds)
        self.init_solr_retry_window()
        for ds in dsets:
            self.verify_published_single_solr(ds)

        for ds in dsets:
            self.tlog("Verifying published to all: %s" % ds.id)
            self.verify.verify_published(ds)

    def publish_single_db(self, ds):
        self.tlog("Publishing to db: %s" % ds.id)
        self.publisher.publish_to_db(ds)

    def unpublish_single_db(self, ds):
        self.tlog("Unpublishing from db: %s" % ds.id)
        self.publisher.unpublish_from_db(ds)

    def publish_single_tds(self, ds):
        self.tlog("Publishing to TDS: %s" % ds.id)
        self.publisher.publish_to_tds(ds)

    def unpublish_single_tds(self, ds):
        self.tlog("Unpublishing from TDS: %s" % ds.id)
        self.publisher.unpublish_from_tds(ds)
    
    def publish_single_tds_no_reinit(self, ds):
        self.tlog("Publishing to TDS: %s" % ds.id)
        self.publisher.publish_to_tds(ds, thredds_reinit=False)
    
    def publish_single_solr(self, ds):
        self.tlog("Publishing to SOLR: %s" % ds.id)
        self.publisher.publish_to_solr(ds)

    def unpublish_single_solr(self, ds):
        self.tlog("Unpublishing from SOLR: %s" % ds.id)
        self.publisher.unpublish_from_solr(ds)

    def verify_published_single_db(self, ds):
        self.tlog("Verifying published to DB: %s" % ds.id)
        self.verify.verify_published(ds, [pl.db],
                                     db_suppress_file_url_checks = True)
        
    def verify_unpublished_single_db(self, ds):
        self.tlog("Verifying unpublished from db: %s" % ds.id)
        self.verify.verify_unpublished(ds, [pl.db])

    def verify_published_single_tds(self, ds):
        self.tlog("Verifying published to TDS: %s" % ds.id)
        self.verify.verify_published(ds, [pl.tds])

    def verify_unpublished_single_tds(self, ds):
        self.tlog("Verifying unpublished from TDS: %s" % ds.id)
        self.verify.verify_unpublished(ds, [pl.tds])


    # The methods verify_[un]published_single_solr include retries. Before calling, 
    # init_solr_retry_window should be called after the last [un]publication event.
    # The relevant verify function can then be called a number of times, and the 
    # retry window will run from the time that init_solr_retry_window was called.

    def init_solr_retry_window(self):
        self.solr_retry_window_start = time.time()

    def verify_published_single_solr(self, ds):
        self.tlog("Verifying published to SOLR: %s" % ds.id)
        self.verify.verify_published(ds, [pl.solr], 
                                     solr_retry=True, 
                                     solr_retry_window_start = self.solr_retry_window_start)

    def verify_unpublished_single_solr(self, ds):
        self.tlog("Verifying unpublished from SOLR: %s" % ds.id)
        self.verify.verify_unpublished(ds, [pl.solr],
                                       solr_retry=True, 
                                       solr_retry_window_start = self.solr_retry_window_start)


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
            self.unpublish_single_solr(ds)

        self.init_solr_retry_window()
        for ds in dsets:
            self.verify_unpublished_single_solr(ds)

        for ds in dsets:
            self.unpublish_single_tds(ds)

        for ds in dsets:
            self.verify_unpublished_single_tds(ds)

        for ds in dsets:
            self.unpublish_single_db(ds)

        for ds in dsets:
            self.verify_unpublished_single_db(ds)

        self.tlog("Verifying unpublished from all: %s" % ds.id)
        self.verify.verify_unpublished(ds)

    def verify_multi(self, verify_single_func, dsets, pool=None):
        if pool:
            self.tlog("Verifying %s datasets in parallel" % len(dsets))
            pool.run(verify_single_func, dsets)
        else:
            for ds in dsets:
                verify_single_func(ds)


    def run_parallel_tests(self, dsets, pool_size, parallel_verify=False):

        pool = PoolWrapper(pool_size,
                           log_func = self.tlog)

        verify_pool = None
        if parallel_verify:
            verify_pool = pool

        # DB
        pool.run(self.publish_single_db, dsets)
        self.verify_multi(self.verify_published_single_db, dsets, verify_pool)
        
        # THREDDS
        # publish all but one in parallel without reinit, then last one 
        # with reinit
        pool.run(self.publish_single_tds_no_reinit, dsets[:-1])
        self.publish_single_tds(dsets[-1])
        self.verify_multi(self.verify_published_single_tds, dsets, verify_pool)

        # SOLR
        pool.run(self.publish_single_solr, dsets)
        self.init_solr_retry_window()
        self.verify_multi(self.verify_published_single_solr, dsets, verify_pool)


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
        self.publish_and_verify(ds1)
        self.publish_and_verify(ds2)
        # self.publish_and_verify([ds1, ds2])
        self.unpublish_and_verify(ds2)
        self.verify_published(ds1)

    def test_7_verify_unpublish_earliest_of_multi_versions(self):
        self.log_starting_test()
        self.ensure_empty()
        # self.publish_and_verify([ds1, ds2])
        self.publish_and_verify(ds1)
        self.publish_and_verify(ds2)
        self.unpublish_and_verify(ds1)
        self.verify_published(ds2)

    def test_8_parallel_publication(self):
        self.log_starting_test()
        dsets = datasets.get_parallel_test_datasets()
        pool_step = int(config.get('partest_pool_size_increment'))
        pool_max = int(config.get('partest_pool_size_max'))
        pool_req = int(config.get('partest_pool_size_required'))
        parallel_verify = config.is_set('partest_parallel_verify')
        try:
            for pool_size in range(pool_step, 1 + pool_max, pool_step):
                self.ensure_empty(dset_list = dsets)
                self.tlog("Starting parallel test for pool size %s" % pool_size)
                try:
                    self.run_parallel_tests(dsets, pool_size, parallel_verify=parallel_verify)
                    self.tlog("Parallel test succeeded for size %s" % pool_size)
                except:
                    self.tlog("Parallel test failed for pool size %s" % pool_size)
                    if pool_size <= pool_req:
                        raise
        finally:
            # the TearDownClass only removes the basic test data, not all the 
            # datasets used in the parallel test, so do it here instead.
            self.ensure_empty(dset_list = dsets)
