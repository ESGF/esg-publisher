# dummy_esgf_publisher.py - used until real ESGF code is connected

## TODO: what other args should be added to these calls?
## When we rig this up to the real publisher code it will become self-explanatory

def publish(dsid, file_list):
    pass

def publish_to_db(dsid, file_list):
    pass

def publish_to_tds(dsid, file_list):
    pass

def publish_to_solr(dsid, file_list):
    pass

def unpublish(dsid, file_list):
    pass

def unpublish_from_db(dsid, file_list):
    pass

def unpublish_from_tds(dsid, file_list):
    pass

def unpublish_from_solr(dsid, file_list):
    pass

def delete_all():
    delete_all_files_from_disk()
    delete_all_from_db()
    delete_all_from_tds()
    delete_all_from_solr()

def delete_all_files_from_disk():
    pass

def delete_all_from_db():
    pass

def delete_all_from_tds():
    pass

def delete_all_from_solr():
    pass
