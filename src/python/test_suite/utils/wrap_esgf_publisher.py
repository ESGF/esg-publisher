from datasets import all_datasets

def publish(ds):
    pass

def publish_to_db(ds):
    pass

def publish_to_tds(ds):
    pass

def publish_to_solr(ds):
    pass

def unpublish(ds):
    unpublish_from_solr(ds)
    unpublish_from_tds(ds)
    unpublish_from_db(ds)

def unpublish_from_db(ds):
    pass

def unpublish_from_tds(ds):
    pass

def unpublish_from_solr(ds):
    pass

def delete_all():
    for ds in all_datasets:
        unpublish(ds)
