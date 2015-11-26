import sys
import traceback
import logging
import time

import info_classes as ic
from datasets import all_datasets

from . import config
import esg_config
import read_database
import read_thredds
import read_index

_esg_conf = esg_config.Config()
_db = read_database.ReadDB(_esg_conf)
_tds = read_thredds.ReadThredds(_esg_conf)
_index = read_index.ReadIndex(_esg_conf)

class VerifyFuncs(object):

    def __init__(self, logger=None):
        if logger == None:
            logger = logging.getLogger()
        self.logger = logger

    def _get_all_verify_funcs(self, publication_levels=None, verify_unpublish=False):
        verify_funcs = []

        for pub_level in publication_levels:
            if pub_level not in ic.PublicationLevels.all():
                raise ic.ESGFPublicationTestError("Publication level not known: %s" % pub_level)

            if verify_unpublish:
                func_name = "self.verify_unpublished_from_%s" % pub_level
            else:
                func_name = "self.verify_published_to_%s" % pub_level

            verify_funcs.append((pub_level, eval(func_name)))

        return verify_funcs

    def verify_published(self, ds, publication_levels=None, **kwargs):
        """
        Verify that a dataset is published to the specified publication levels.

        any keyword arguments for particular levels should be passed in with the 
        level name and an underscore prepended, e.g. send in 
        db_suppress_file_url_checks=... for the arg suppress_file_url_checks=... on 
        verify_published_to_db
        """
        return self._verify_dataset_status(ds, False, publication_levels, **kwargs)

    def verify_unpublished(self, ds, publication_levels=None, **kwargs):
        return self._verify_dataset_status(ds, True, publication_levels, **kwargs)

    def subset_dict(self, d, prefix):
        """
        subset a dictionary to those keys that are strings beginning with specified prefix, 
        removing the prefix in the output dictionary
        """
        dout = {}
        pos = len(prefix)
        for k in d:
            if isinstance(k, basestring) and len(k) > pos:
                if k.startswith(prefix):
                    dout[k[pos:]] = d[k]
        return dout

    def _verify_dataset_status(self, ds, verify_unpublish, publication_levels, **kwargs):

        if not publication_levels:
            publication_levels = ic.PublicationLevels.all()

        verify_funcs = self._get_all_verify_funcs(publication_levels=publication_levels, 
                                                  verify_unpublish=verify_unpublish)
        if verify_unpublish:
            descrip = "unpublished"
        else:
            descrip = "published"

        for pub_level, verify_func in verify_funcs:
            kwargs_this_level = self.subset_dict(kwargs, "%s_" % pub_level)
            try:
                self.logger.debug("func=%s, ds=%s kwargs=%s" % (verify_func.__name__, ds, kwargs_this_level))
                verify_func(ds, **kwargs_this_level)
            except:
                e, msg, tb = sys.exc_info()
                self.logger.debug(msg)
                for line in traceback.format_tb(tb):
                    self.logger.debug(line)
                raise ic.ESGFPublicationVerificationError("Cannot verify that dataset was %s. "
                    "DSID: %s, Level: %s" % (descrip, ds.id, verify_func.func_name.split("_")[-1]))
        self.logger.info("Verified that dataset was %s: DSID: %s, Levels: %s" % 
                         (descrip, ds.id, publication_levels))
        return True


    def verify_published_to_db(self, ds, suppress_file_url_checks=False):

        if config.is_set("devel_skip_verify_published_to_db"): 
            self.logger.warn("skipping verify_published_to_db")
            return

        self.logger.debug("doing verify_published_to_db: %s" % ds.id)
        
        # Checks database has dataset record with 
        # related file records matching those referenced inside ds object
        ds_db = _db.get_dset(ds.name, ds.version, 
                             suppress_file_url_checks = suppress_file_url_checks)
        if ds != ds_db:
            self.logger.debug("from fs: %s" % ds)
            self.logger.debug("from db: %s" % ds_db)
            raise Exception("database has wrong info")
        # 
        # For good measure, look up files by tracking ID.  The above
        # comparison has already included files, so really, it only
        # checks that tracking IDs are not duplicated.  The get_file()
        # is really more relevant in verify_unpublished_from_db below.
        for f in ds.files:
            assert f == _db.get_file(f.tracking_id,
                                     suppress_url_checks = suppress_file_url_checks)

        self.logger.debug("done verify_published_to_db: %s" % ds.id)


    def verify_published_to_tds(self, ds):

        if config.is_set("devel_skip_verify_published_to_tds"): 
            self.logger.warn("skipping verify_published_to_tds")
            return

        self.logger.debug("doing verify_published_to_tds: %s" % ds.id)

        # Checks TDS has dataset record with 
        # related file records matching those referenced inside ds object
        if not ds.catalog_location:
            self.logger.info("rechecking DB to get THREDDS catalog location")
            _db.get_catalog_location(ds)
        self.logger.debug("catalog location: %s" % ds.catalog_location)

        check_catalog_xml = not config.is_set("devel_skip_catalog_xml")

        local_path = _tds.local_path(ds.catalog_location)
        ds_tds_local = _tds.parse_catalog(local_path)
        assert ds == ds_tds_local  # check local THREDDS catalog has correct info

        if check_catalog_xml:
            assert catalog_location == _tds.get_catalog_location_via_local(ds.id) # check listed in local catalog.xml

        url_path = _tds.url_path(ds.catalog_location)
        ds_tds_served = _tds.parse_catalog(url_path)
        assert ds == ds_tds_served  #  check THREDDS catalog as served over http has correct info

        if check_catalog_xml:
            assert catalog_location == _tds.get_catalog_location_via_http(ds.id)  # check listed in catalog.xml as served over http

        self.logger.debug("done verify_published_to_tds: %s" % ds.id)

    def _get_solr_retry_times(self, 
                              default_max_time=120, 
                              default_sleep_time=5):
        
        max_time = float(config.get_with_default('solr_verify_max_time',
                                                 default_max_time))

        sleep_time = float(config.get_with_default('solr_verify_sleep_time',
                                                   default_sleep_time))

        end_time = time.time() + max_time

        return end_time, sleep_time

    def verify_published_to_solr(self, ds, retry=True):

        self.logger.debug("doing verify_published_to_solr: %s" % ds.id)

        if config.is_set("devel_skip_verify_published_to_solr"): 
            self.logger.warn("skipping verify_published_to_solr")
            return

        # Checks SOLR has dataset record with 
        # related file records matching those referenced inside ds object

        end_time, sleep_time = self._get_solr_retry_times()
        while True:
            check_start_time = time.time()
            self.logger.debug("looking for dataset in SOLR")
            try:
                ds_index = _index.get_dset(ds.name, ds.version)
            except read_index.NotFound:
                pass
            else:
                break
            if check_start_time > end_time or not retry:
                self.logger.debug("giving up looking for dataset in SOLR")
                raise read_index.NotFound
            time.sleep(sleep_time)

        assert ds == ds_index  # check data in SOLR has correct info

        self.logger.debug("done verify_published_to_solr: %s" % ds.id)


    def verify_unpublished_from_db(self, ds):

        if config.is_set("devel_skip_verify_unpublished_from_db"): 
            self.logger.warn("skipping verify_unpublished_from_db")
            return

        self.logger.debug("doing verify_unpublished_from_db: %s" % ds.id)

        # NOTE: this is not simply "not verify_published_to_db()"
        # We want to verify ALL content is not there
        # Any partial match should raise an Exception

        # - assert dataset id is not in database
        # - assert no files from file_list have records in the DB
        #   (any such records could not be connected to dataset as
        #   this would violate foreign key constraint on
        #   dataset_file_version, but they could be orphaned, so look
        #   for them by their tracking ID)
        try:
            _db.get_dset(ds.name, ds.version)
        except read_database.NotFound:
            pass
        else:
            raise Exception("could not verify %s unpublished" % ds.id)
        for f in ds.files:
            try:
                _db.get_file(f.tracking_id)
            except read_database.NotFound:
                pass
            else:
                raise Exception("could not verify %s (contained in %s) unpublished" % (f.url, ds.id))

        self.logger.debug("done verify_unpublished_from_db: %s" % ds.id)


    def verify_unpublished_from_tds(self, ds, check_known_location=True):

        if config.is_set("devel_skip_verify_unpublished_from_tds"): 
            self.logger.warn("skipping verify_unpublished_from_tds")
            return

        self.logger.debug("doing verify_unpublished_from_tds: %s" % ds.id)

        # NOTE: this is not simply "not verify_published_to_tds()"
        # We want to verify ALL content is not there
        # Any partial match should raise an Exception
        #
        # - assert there is not a TDS XML record for dataset id
        #
        # By default, it will check the known catalog location that has
        # been stored in the 'ds' object by an earlier call to
        # verify_published_to_db().  If that location is not stored, then
        # an exception is raised.
        #
        # In contexts *other* than checking whether it has been
        # unpublished from the previous known location, call with 
        # 'check_known_location=False' to suppress this check.
        #
        # Additionally, a check is made whether the dataset exists in the
        # top-level catalog.

        if check_known_location:
            try:
                catalog_location = ds.catalog_location
            except AttributeError:
                raise Exception("catalog location has not been stored")

            for path in [_tds.local_path(catalog_location),
                         _tds.url_path(catalog_location)]:
                try:
                    _tds.parse_catalog(path)
                except read_thredds.NotFound:
                    pass
                else:
                    raise Exception("%s should have been unpublished" % local_path)

        if not config.is_set("devel_skip_catalog_xml"):

            try:
                _tds.get_catalog_location_via_local(ds.id)
            except read_thredds.NotFound:
                pass
            else:
                raise Exception("%s still found in catalog.xml (locally)" % ds.id)

            try:
                _tds.get_catalog_location_via_http(ds.id)
            except read_thredds.NotFound:
                pass
            else:
                raise Exception("%s still found in catalog.xml (via http)" % ds.id)

        self.logger.debug("done verify_unpublished_from_tds: %s" % ds.id)


    def verify_unpublished_from_solr(self, ds, retry=True):

        if config.is_set("devel_skip_verify_unpublished_from_solr"): 
            self.logger.warn("skipping verify_unpublished_from_solr")
            return

        self.logger.debug("doing verify_unpublished_from_solr: %s" % ds.id)

        # NOTE: this is not simply "not verify_published_to_solr()"
        # We want to verify ALL content is not there
        # Any partial match should raise an Exception

        # - assert dataset id is not in solr (The check below is for
        # the dataset, but as implemented in read_index.py, the actual
        # request will check for files with that dataset ID ("any"
        # files, rather than asking about known files).  If there are
        # none, it is taken that the dataset ID does not exist in
        # Solr.  At present, I don't know of a way if an 'empty'
        # dataset can exist in Solr or how this would be checked.)

        end_time, sleep_time = self._get_solr_retry_times()
        while True:
            check_start_time = time.time()
            self.logger.debug("looking for (absence of) dataset in SOLR")
            try:
                _index.get_dset(ds.name, ds.version)
            except read_index.NotFound:
                break
            if check_start_time > end_time or not retry:
                self.logger.debug("giving up looking for (absence of) dataset in SOLR")
                raise Exception("could not verify %s unpublished" % ds.id)
            time.sleep(sleep_time)

        self.logger.debug("done verify_unpublished_from_solr: %s" % ds.id)    


    def verify_empty_of_test_data(self):

        self.logger.debug("doing verify_empty_of_test_data")
        for ds in all_datasets:
            self.verify_unpublished_from_db(ds)
            self.verify_unpublished_from_tds(ds, check_known_location = False)
            self.verify_unpublished_from_solr(ds)
        self.logger.debug("done verify_empty_of_test_data")
