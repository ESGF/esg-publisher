import unittest
import logging
import inspect
import sys
import time
import traceback
import string

from utils import config
from utils.info_classes import PublicationLevels as pl
import utils.verify as verify
import utils.datasets as datasets
import utils.wrap_esgf_publisher as publisher

from utils.parallel_procs import PoolWrapper

ds1 = datasets.d1v1
ds2 = datasets.d1v2


def with_log_status(func):
    def func_wrapper(cls):
        print func.__name__
        caller_name = func.__name__
        cls.tlog("\n=== %s: STARTING ===\n" % caller_name)
        try:
            rv = func(cls)
            cls.tlog("\n=== %s: SUCCESS ===\n" % caller_name)
            return rv
        except:
            cls.tlog("\n=== %s: FAIL ===\n" % caller_name, log_level="warn")
            raise
    return func_wrapper


class PublisherTests(unittest.TestCase):

    @classmethod
    def tlog(cls, msg, log_level="info", show_method = False):
        if show_method:
            meth_name = inspect.stack()[1][0].f_code.co_name
            msg = "%s: %s" % (meth_name, msg)
        cls.logger.log(getattr(logging, log_level.upper()), msg)

    def with_log_threshold(self, level, func, *args, **kwargs):
        "Run a function, while temporarily setting the logging level to specified value"
        old = self.logger.level
        if level:
            self.logger.setLevel(level)
        try:
            rv = func(*args, **kwargs)
        finally:
            self.logger.setLevel(old)
        return rv

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
        cls.tlog("Verifying no test data published")
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


    def _publish_parallel_and_verify(self, dsets, level, pool):
        if level == 'db':
            pool.run(self.publish_single_db, dsets)
        elif level == 'tds':
            pool.run(self.publish_single_tds_no_reinit, dsets[:-1])
            self.publish_single_tds(dsets[-1])
        elif level == 'solr':
            pool.run(self.publish_single_solr, dsets)
            self.init_solr_retry_window()
        else:
            raise ValueError

        v_func = getattr(self, 'verify_published_single_' + level)
        for ds in dsets:
            v_func(ds)

    def _unpublish_parallel_and_verify(self, dsets, level, pool):
        if level == 'db':
            pool.run(self.unpublish_single_db, dsets)
        elif level == 'tds':
            self.tlog("TDS parallel unpublish not implemented - using unpublish with use-list")
            self.publisher.unpublish_from_tds_multi(dsets)
        elif level == 'solr':
            pool.run(self.unpublish_single_solr, dsets)
            self.init_solr_retry_window()
        else:
            raise ValueError

        v_func = getattr(self, 'verify_unpublished_single_' + level)
        for ds in dsets:
            v_func(ds)

    parallel_log_threshold = None

    def publish_parallel_and_verify(self, dsets, level, pool):
        self.with_log_threshold(self.parallel_log_threshold, self._publish_parallel_and_verify, dsets, level, pool)

    def unpublish_parallel_and_verify(self, dsets, level, pool):
        self.with_log_threshold(self.parallel_log_threshold, self._unpublish_parallel_and_verify, dsets, level, pool)

    def parallel_publish_unpublish_for_pub_level(self, dsets, level, pool):

        self.tlog("Starting parallel publication test for %s datasets at level %s with pool size %s" % (len(dsets), level, len(pool)))

        t = time.time()
        self.publish_parallel_and_verify(dsets, level, pool)
        self.tlog("time to publish all %s dsets to %s with pool size %s: %ss" % (
                len(dsets), level, len(pool), time.time() - t))

        self.tlog("Starting parallel unpublication test for level %s with pool size %s" % (level, len(pool)))
        t = time.time()
        self.unpublish_parallel_and_verify(dsets, level, pool)
        self.tlog("time to unpublish all %s dsets from %s with pool size %s: %ss" % (
                len(dsets), level, len(pool), time.time() - t))

    def get_pool(self, pool_size):
        return PoolWrapper(pool_size, log_func = self.tlog)

    def run_parallel_tests(self, dsets, pool_sizes):
        """
        Runs parallel publication and unpublication on a number of datasets. 
        pool_sizes should be list in increasing order of number of simultaneous processes to try.

        It will publish all to db and test, then unpublish and test, until it breaks or the max 
        size is reached.  Then it will, if necessary clean up from failure and republish all, using 
        a conservative pool size, before doing the same for TDS and then Solr.

        Finally unpublishes.
        """
        failure_encountered = False
        for level in 'db', 'tds', 'solr':
            max_ok = 0  # largest successful pool size
            for pool_size in pool_sizes:
                try:
                    pool = self.get_pool(pool_size)
                    self.parallel_publish_unpublish_for_pub_level(dsets, level, pool)
                    max_ok = pool_size
                except:
                    exc_info = sys.exc_info()
                    self.tlog("Parallel test failed for pool size %s: %s\n%s" % 
                              (pool_size, exc_info[1], string.join(traceback.format_tb(exc_info[2]))))
                    failure_encountered = True
                    break

            pool = self.get_pool(max(max_ok / 3, 1))
            if failure_encountered:
                self.tlog("Clearing up from %s after failed parallel publication" % level)
                self.unpublish_parallel_and_verify(dsets, level, pool)
            self.tlog("Republishing to %s" % level)
            self.publish_parallel_and_verify(dsets, level, pool)

        pool = self.get_pool(2)
        for level in 'solr', 'tds', 'db':
            self.unpublish_parallel_and_verify(dsets, level, pool)

    @with_log_status
    def test_1_verify_publish_single_dataset_single_version(self):
        self.ensure_empty()
        self.publish_and_verify(ds1)
        
    @with_log_status
    def test_2_verify_publish_single_dataset_two_versions(self):
        self.ensure_empty()
        self.publish_and_verify(ds1)
        self.publish_and_verify(ds2)
        self.verify_published(ds1)
    
    @with_log_status
    def test_3_verify_publish_all_in_stages(self):
        self.ensure_empty()
        self.publish_and_verify([ds1, ds2])
    
    @with_log_status
    def test_4a_verify_publish_in_reverse(self):
        self.ensure_empty()
        self.publish_and_verify(ds2)
        self.publish_and_verify(ds1)
        self.verify_published(ds2)
        
    @with_log_status
    def test_4b_verify_publish_in_reverse_in_stages(self):   
        self.ensure_empty()
        self.publish_and_verify([ds2, ds1])

    @with_log_status
    def test_5_verify_unpublish_sole_version(self):
        self.ensure_empty()
        self.publish_and_verify(ds1)
        self.unpublish_and_verify(ds1)

    @with_log_status
    def test_6_verify_unpublish_latest_of_multi_versions(self):
        self.ensure_empty()
        self.publish_and_verify(ds1)
        self.publish_and_verify(ds2)
        self.unpublish_and_verify(ds2)
        self.verify_published(ds1)

    @with_log_status
    def test_7_verify_unpublish_earliest_of_multi_versions(self):
        self.ensure_empty()
        self.publish_and_verify(ds1)
        self.publish_and_verify(ds2)
        self.unpublish_and_verify(ds1)
        self.verify_published(ds2)

    @with_log_status
    def test_8_parallel_publication(self):
        dsets = datasets.get_parallel_test_datasets()
        pool_step = int(config.get('partest_pool_size_increment'))
        pool_max = int(config.get('partest_pool_size_max'))

        try:
            self.parallel_log_threshold = getattr(logging, config.get('partest_log_level'))
        except KeyError:
            pass

        pool_sizes = range(pool_step, 1 + pool_max, pool_step)

        self.ensure_empty(dset_list = dsets)
        try:
            self.run_parallel_tests(dsets, pool_sizes)
        finally:
            # the TearDownClass only removes the basic test data, not all the 
            # datasets used in the parallel test, so do it here instead.
            self.ensure_empty(dset_list = dsets)
