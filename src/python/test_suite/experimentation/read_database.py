import os
import psycopg2
import string

from publication_objects import Dataset, File


class NotFound(Exception):
    pass


class TalkToDB(object):

    def __init__(self, 
                 db_name = 'esgcet', 
                 db_user = 'esgcet',
                 db_host = None, 
                 db_port = None):

        self.con = psycopg2.connect(database=db_name, 
                                    user=db_user, 
                                    host=db_host, 
                                    port=db_port)
        self.cur = self.con.cursor()

    def get_output(self, command):
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
            assert len(output) == 1
            return output[0]

        elif max_one_row:
            assert len(output) <= 1
            if output:
                return output[0]
            else:
                return None            
        else:
            return output


    def get_dset(self, dataset_id, version):
        """
        returns a 2-tuple Dataset object, catalog_location
        corresponding to the dataset in the DB.

        Raises NotFound if it isn't there
        """

        dsvid = self.select('id', 'dataset_version', 
                            where = "name ='%s.v%d'" % (dataset_id, version),
                            max_one_row = True)
        if dsvid == None:
            raise NotFound

        ds = Dataset(dataset_id, version)

        catalog_location = \
            self.select('location', 'catalog', 
                        where = "dataset_name = '%s' and version = %s" % 
                        (dataset_id, version),
                        exactly_one_row = True)
            
        fvids = self.select('file_version_id', 'dataset_file_version',
                            where = "dataset_version_id = %s" % dsvid)

        for fvid in fvids:
            location, size, cksum, tracking_id = \
                self.select(('location', 'size', 'checksum', 'tracking_id'), 
                            'file_version',
                            where = "id = %s" % fvid,
                            exactly_one_row = True)
            name = os.path.basename(location)
            ds.add_file(File(name, size, cksum, tracking_id))

        return ds, catalog_location


if __name__ == '__main__':
    name = 'cmip5.output1.CSIRO-QCCCE.CSIRO-Mk3-6-0.historical.mon.land.Lmon.r5i1p1'
    version = 1
    ds, catalog_location = TalkToDB().get_dset(name, version)
    print ds
    print catalog_location
