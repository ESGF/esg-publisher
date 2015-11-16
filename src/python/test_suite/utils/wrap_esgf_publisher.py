from datasets import all_datasets

import subprocess

def publish(ds):
    publish_to_db(ds)
    publish_to_tds(ds)
    publish_to_solr(ds)

def publish_to_db(ds):
    run_command("esgpublish",
                "--new-version", str(ds.version),
                "--project", ds.id.split(".")[0],
                "--map", ds.mapfile_path)

def publish_to_tds(ds):
    run_command("esgpublish", 
                "--new-version", str(ds.version),
                "--noscan",
                "--thredds",
                "--service", "fileservice",
                "--use-existing", format_name(ds))

def publish_to_solr(ds):
    run_command("esgpublish", 
                "--new-version", str(ds.version),
                "--noscan",
                "--publish",
                "--use-existing", "%s#%s" % format_name(ds))

def unpublish(ds):
    try:
        verify_unpublished_from_solr(ds)
    except:
        unpublish_from_solr(ds)
    try:
        verify_unpublished_from_tds(ds)
    except:
        unpublish_from_tds(ds)
    try:
        verify_unpublished_from_db(ds)
    except:
        unpublish_from_db(ds)

def unpublish_from_db(ds):
    run_command("esgunpublish",
                "--database-only",
                "--no-republish",
                format_name(ds))

def unpublish_from_tds(ds):
    run_command("esgunpublish",
                "--skip-index",
                "--no-republish",
                format_name(ds))
                
def unpublish_from_solr(ds):
    run_command("esgunpublish",
                "--skip-thredds",
                "--no-republish",
                format_name(ds))
                
def delete_all():
    for ds in all_datasets:
        unpublish(ds)

def format_name(ds):
    return "%s#%s" % (ds.name, ds.version)

def run_command(*command):
    print "FIXME: insert code to actually run ", command
