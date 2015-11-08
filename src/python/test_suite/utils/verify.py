import utils.info_classes as ic
import utils.datasets as datasets

def get_pub_base_dir(dsid):
    return

def get_file_list(dsid):
    for dataset in datasets.all_datasets:
        if dataset.id == dsid:
            return dataset.files

    raise ic.ESGFPublicationTestError("Cannot find files for dataset id: %s" % dsid)

def get_all_verify_funcs(publication_levels=None):
    verify_funcs = []

    for pub_level in publication_levels:
        if pub_level not in ic.PublicationLevels.all():
            raise ic.ESGFPublicationTestError("Publication level not known: %s" % pub_level)

        if pub_level == "disk":
            func_name = "verify_files_on_disk"
        else:
            func_name = "verify_published_to_%s" % pub_level

        verify_funcs.append(eval(func_name))

    return verify_funcs

def verify_dataset_published(dsid, publication_levels=None):

    if not publication_levels:
        publication_levels = ic.PublicationLevels.all()

    verify_funcs = get_all_verify_funcs(publication_levels=publication_levels)

    file_list = get_file_list(dsid)
    assert file_list # Check exists

    for verify_func in verify_funcs:
        try:
            verify_func(dsid, file_list)
        except:
            raise ic.ESGFPublicationVerificationError("Cannot verify that dataset was published. "
                "DSID: %s, Level: %s" % (dsid, verify_func.func_name.split("_")[-1]))

    return True

def verify_files_on_disk(dsid, file_list):
    # Checks files are on disk
    return True

def verify_published_to_db(dsid, file_list):
    # Checks database has dataset record with related file records matching file_list
    return True

def verify_published_to_tds(dsid, file_list):
    # Checks TDS has dataset record with related file records matching file_list
    return True

def verify_published_to_solr(dsid, file_list):
    # Checks SOLR has dataset record with related file records matching file_list
    return True

def verify_dataset_unpublished(dsid):

    verify_funcs = (verify_unpublished_from_solr,
                    verify_unpublished_from_db,
                    verify_unpublished_from_tds,
                    verify_files_not_on_disk)

    file_list = get_file_list(dsid)
    assert file_list # Check exists

    for verify_func in verify_funcs:
        try:
            verify_func(dsid, file_list)
        except:
            raise ic.ESGFPublicationVerificationError("Cannot verify that dataset was unpublished. "
                "DSID: %s, Level: %s" % (dsid, verify_func.func_name.split("_")[-1]))

    return True

def verify_files_not_on_disk(dsid, file_list):
    # NOTE: this is not simply "not verify_files_on_disk()"
    # We want to verify ALL content is not there
    # Any partial match should raise an Exception

    # TODO:
    # - assert no files are on disk from file_list (following DRS structure from dataset id)
    pass

def verify_unpublished_from_db(dsid, file_list):
    # NOTE: this is not simply "not verify_published_to_db()"
    # We want to verify ALL content is not there
    # Any partial match should raise an Exception

    # TODO:
    # - assert dataset id is not in database
    # - assert no files from file_list have records in the DB that are connected to dataset id
    pass

def verify_unpublished_from_tds(dsid, file_list):
    # NOTE: this is not simply "not verify_published_to_tds()"
    # We want to verify ALL content is not there
    # Any partial match should raise an Exception

    # TODO:
    # - assert there is not a TDS XML record for dataset id
    # - assert no file XML records exist in TDS from file_list that are connected to dataset id
    pass

def verify_unpublished_from_solr(dsid, file_list):
    # NOTE: this is not simply "not verify_published_to_solr()"
    # We want to verify ALL content is not there
    # Any partial match should raise an Exception

    # TODO:
    # - assert dataset id is not in solr
    # - assert no files from file_list are in solr with connections to dataset id
    pass

def verify_empty():
    verify_no_files_on_disk()
    verify_db_empty()
    verify_tds_empty()
    verify_solr_empty()

def verify_no_files_on_disk():
    empty = True
    if not empty:
        raise ic.ESGFPublicationTestError("Test file system is not empty!")

def verify_db_empty():
    empty = True
    if not empty:
        raise ic.ESGFPublicationTestError("Test DB is not empty!")

def verify_tds_empty():
    empty = True
    if not empty:
        raise ic.ESGFPublicationTestError("Test TDS is not empty!")

def verify_solr_empty():
    empty = True
    if not empty:
        raise ic.ESGFPublicationTestError("Test SOLR system is not empty!")
