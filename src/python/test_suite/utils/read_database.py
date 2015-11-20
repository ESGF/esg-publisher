import psycopg2
import urlparse
import string

from publication_objects import Dataset, File


class NotFound(Exception):
    pass


class ReadDB(object):

    def __init__(self, conf):

        self.db_url = conf.get_db_url()
        self.con = None

    def ensure_connected(self):
        if self.con and not self.con.closed:
            return
        result = urlparse.urlparse(self.db_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        self.con = psycopg2.connect(
            database = database,
            user = username,
            password = password,
            host = hostname
            )
        self.cur = self.con.cursor()
        

    def get_output(self, command):
        self.ensure_connected()
        self.cur.execute(command)
        return self.cur.fetchall()

    def select(self, fields, table, where=None, 
               max_one_row=False, 
               exactly_one_row=False):
        """
        returns select output 

        e.g. select(('project', 'name'), 'dataset', where=('id', 12345))
        does SELECT project, name from dataset where id = 1235;
        
        'where' if set, is a string that is passed to the select
        (not including the word "where" itself)

        If input 'fields' is just a string rather than a list/tuple,
        then return each row as a single value rather than as a tuple

        If exactly_one_row = True, assert this, and return the one row
        instead of a list.

        If max_one_row = True, assert this, and return either that one row or 
        the None value, instead of a list.
        """
        single_col = False
        if isinstance(fields, basestring):
            fields = (fields,)
            single_col = True

        fields_spec = string.join(fields, ",")
        command = 'SELECT %s from %s' % (fields_spec,
                                         table)
        
        if where:
            command += " where " + where

        output = self.get_output(command)

        if single_col:
            output = [row[0] for row in output]

        if exactly_one_row:
            if len(output) != 1:
                raise Exception("expected 1 match from '%s' - got %s" % (command, len(output)))
            return output[0]

        elif max_one_row:
            if len(output) > 1:
                raise Exception("expected <=1 match from '%s' - got %s" % (command, len(output)))
            if output:
                return output[0]
            else:
                return None            
        else:
            return output


    def get_file(self, tracking_id,
                 suppress_url_checks=False):
        """
        Gets a File object by its tracking ID.  Raises NotFound if absent.
        Raises some other exception if it is duplicated.
        """
        
        result = self.select(('url', 'size', 'checksum',), 
                             'file_version',
                             where = "tracking_id = '%s'" % tracking_id,
                             max_one_row = True)
        if result == None:
            raise NotFound

        url, size, cksum = result
        
        return File(url, size, cksum, tracking_id,
                    suppress_url_checks=suppress_url_checks)


    def get_catalog_location(self, ds, missing_okay=False):
        """
        get thredds catalog location for a dataset object, and 
        store it in the object
        """
        if missing_okay:
            kwargs = {'max_one_row': True}
        else:
            kwargs = {'exactly_one_row': True}
        
        catalog_location = self.select('location', 'catalog', 
                                       where = "dataset_name = '%s' and version = %s" % 
                                       (ds.name, ds.version),
                                       **kwargs)
        if catalog_location:
            ds.catalog_location = catalog_location
        else:
            ds.catalog_location = False

    def get_dset(self, dataset_id, version, suppress_file_url_checks=False):
        """
        returns a Dataset object
        corresponding to the dataset in the DB.

        Raises NotFound if it isn't there
        """

        dsvid = self.select('id', 'dataset_version', 
                            where = "name ='%s.v%d'" % (dataset_id, version),
                            max_one_row = True)
        if dsvid == None:
            raise NotFound

        ds = Dataset(dataset_id, version)

        self.get_catalog_location(ds, missing_okay=True)

        fvids = self.select('file_version_id', 'dataset_file_version',
                            where = "dataset_version_id = %s" % dsvid)

        for fvid in fvids:
            url, size, cksum, tracking_id = \
                self.select(('url', 'size', 'checksum', 'tracking_id'), 
                            'file_version',
                            where = "id = %s" % fvid,
                            exactly_one_row = True)
            ds.add_file(File(url, size, cksum, tracking_id,
                             suppress_url_checks=suppress_file_url_checks))

        return ds


if __name__ == '__main__':

    import esg_config

    name = 'cmip5.output1.CSIRO-QCCCE.CSIRO-Mk3-6-0.historical.mon.land.Lmon.r5i1p1'
    version = 1
    conf = esg_config.Config()
    db = ReadDB(conf)
    ds = db.get_dset(name, version)
    print ds
    print ds.catalog_location

    for f in ds.files:
        assert f == db.get_file(f.tracking_id)

    try:
        print db.get_file("blah")
    except NotFound:
        pass
    else:
        raise Exception("'blah' should not have been found")
