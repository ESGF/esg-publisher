import info_classes as ic
from datasets import all_datasets


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

def verify_dataset_published(ds, publication_levels=None):

    if not publication_levels:
        publication_levels = ic.PublicationLevels.all()

    verify_funcs = get_all_verify_funcs(publication_levels=publication_levels)

    for verify_func in verify_funcs:
        try:
            verify_func(ds)
        except:
            raise ic.ESGFPublicationVerificationError("Cannot verify that dataset was published. "
                "DSID: %s, Level: %s" % (ds, verify_func.func_name.split("_")[-1]))

    return True

def verify_files_on_disk(ds):
    # Checks files are on disk
    pass

def verify_published_to_db(ds):
    # Checks database has dataset record with 
    # related file records matching those referenced inside ds object
    pass

def verify_published_to_tds(ds):
    # Checks TDS has dataset record with 
    # related file records matching those referenced inside ds object
    pass

def verify_published_to_solr(ds):
    # Checks SOLR has dataset record with 
    # related file records matching those referenced inside ds object
    pass

def verify_dataset_unpublished(ds):

    verify_funcs = (verify_unpublished_from_solr,
                    verify_unpublished_from_db,
                    verify_unpublished_from_tds)

    for verify_func in verify_funcs:
        try:
            verify_func(ds)
        except:
            raise ic.ESGFPublicationVerificationError("Cannot verify that dataset was unpublished. "
                "DSID: %s, Level: %s" % (ds, verify_func.func_name.split("_")[-1]))

    return True

def verify_unpublished_from_db(ds):
    # NOTE: this is not simply "not verify_published_to_db()"
    # We want to verify ALL content is not there
    # Any partial match should raise an Exception

    # TODO:
    # - assert dataset id is not in database
    # - assert no files from file_list have records in the DB that are connected to dataset id
    pass

def verify_unpublished_from_tds(ds):
    # NOTE: this is not simply "not verify_published_to_tds()"
    # We want to verify ALL content is not there
    # Any partial match should raise an Exception

    # TODO:
    # - assert there is not a TDS XML record for dataset id
    # - assert no file XML records exist in TDS from file_list that are connected to dataset id
    pass

def verify_unpublished_from_solr(ds):
    # NOTE: this is not simply "not verify_published_to_solr()"
    # We want to verify ALL content is not there
    # Any partial match should raise an Exception

    # TODO:
    # - assert dataset id is not in solr
    # - assert no files from file_list are in solr with connections to dataset id
    pass

def verify_empty_of_test_data():
    for ds in all_datasets:
        verify_unpublished_from_db(ds)
        verify_unpublished_from_tds(ds)
        verify_unpublished_from_solr(ds)
