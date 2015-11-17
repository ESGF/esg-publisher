import logging

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

            verify_funcs.append(eval(func_name))

        return verify_funcs

    def verify_published(self, ds, publication_levels=None):
        return self._verify_dataset_status(ds, False, publication_levels)

    def verify_unpublished(self, ds, publication_levels=None):
        return self._verify_dataset_status(ds, True, publication_levels)

    def _verify_dataset_status(self, ds, verify_unpublish, publication_levels):

        if not publication_levels:
            publication_levels = ic.PublicationLevels.all()

        verify_funcs = self._get_all_verify_funcs(publication_levels=publication_levels, 
                                                  verify_unpublish=verify_unpublish)
        if verify_unpublish:
            descrip = "unpublished"
        else:
            descrip = "published"

        for verify_func in verify_funcs:
            try:
                verify_func(ds)
            except:
                raise ic.ESGFPublicationVerificationError("Cannot verify that dataset was %s. "
                    "DSID: %s, Level: %s" % (descrip, ds.id, verify_func.func_name.split("_")[-1]))
        self.logger.info("Verified that dataset was %s: DSID: %s, Levels: %s" % 
                         (descrip, ds.id, publication_levels))
        return True


    def verify_published_to_db(self, ds):

        if config.is_set("devel_skip_verify_published_to_db"): 
            self.logger.warn("skipping verify_published_to_db")
            return

        self.logger.debug("doing verify_published_to_db: %s" % ds.id)
        
        # Checks database has dataset record with 
        # related file records matching those referenced inside ds object
        ds_db, catalog_loc = _db.get_dset(ds.name, ds.version)
        ds.catalog_loc = catalog_loc  # for subsequent verify_published_to_tds
        assert ds == ds_db   #  check database has correct info
        # 
        # For good measure, look up files by tracking ID.  The above comparison 
        # has already included files, so really, it only checks that tracking IDs are 
        # not duplicated.  The get_file() is really more relevant in
        # verify_unpublished_from_db below.
        for f in ds.files:
            assert f == _db.get_file(f.tracking_id)

        self.logger.debug("done verify_published_to_db: %s" % ds.id)


    def verify_published_to_tds(self, ds):

        if config.is_set("devel_skip_verify_published_to_tds"): 
            self.logger.warn("skipping verify_published_to_tds")
            return

        self.logger.debug("doing verify_published_to_tds: %s" % ds.id)

        # Checks TDS has dataset record with 
        # related file records matching those referenced inside ds object
        try:
            catalog_loc = ds.catalog_loc
        except AttributeError:
            raise Exception("verify_published_to_tds() called without first finding catalog location in db via verify_published_to_db()")

        check_catalog_xml = not config.is_set("devel_skip_catalog_xml")

        local_path = _tds.local_path(catalog_loc)
        ds_thredds_local = _tds.parse_catalog(local_path)
        assert ds == ds_tds_local  # check local THREDDS catalog has correct info

        if check_catalog_xml:
            assert catalog_log == _tds.get_catalog_location_via_local(ds.id) # check listed in local catalog.xml

        url_path = _tds.url_path(catalog_loc)
        ds_tds_served = _tds.parse_catalog(url_path)
        assert ds == ds_tds_served  #  check THREDDS catalog as served over http has correct info

        if check_catalog_xml:
            assert catalog_log == _tds.get_catalog_location_via_http(ds.id)  # check listed in catalog.xml as served over http

        self.logger.debug("done verify_published_to_tds: %s" % ds.id)


    def verify_published_to_solr(self, ds):

        self.logger.debug("doing verify_published_to_solr: %s" % ds.id)

        if config.is_set("devel_skip_verify_published_to_solr"): 
            self.logger.warn("skipping verify_published_to_solr")
            return

        # Checks SOLR has dataset record with 
        # related file records matching those referenced inside ds object
        ds_index = _index.get_dset(ds.name, ds.version)
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
                catalog_loc = ds.catalog_loc
            except AttributeError:
                raise Exception("catalog location has not been stored")

            for path in [_tds.local_path(catalog_loc),
                         _tds.url_path(catalog_loc)]:
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


    def verify_unpublished_from_solr(self, ds):

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

        try:
            _index.get_dset(ds.name, ds.version)
        except read_index.NotFound:
            pass
        else:
            raise Exception("could not verify %s unpublished" % ds.id)

        self.logger.debug("done verify_unpublished_from_solr: %s" % ds.id)    


    def verify_empty_of_test_data(self):

        self.logger.debug("doing verify_empty_of_test_data")
        for ds in all_datasets:
            self.verify_unpublished_from_db(ds)
            self.verify_unpublished_from_tds(ds, check_known_location = False)
            self.verify_unpublished_from_solr(ds)
        self.logger.debug("done verify_empty_of_test_data")
