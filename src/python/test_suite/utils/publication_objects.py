import string


"""
Classes to store the information that we want to compare 
between datasets when validating publication in the test suite.
"""

class Dataset(object):

    def __init__(self, name, version, files = None, mapfile_path = None):
        self.name = name
        self.version = int(version)
        self.id = "%s.v%d" % (name, self.version)
        self.mapfile_path = mapfile_path
        self.catalog_location = None
        if files:
            self.files = files
            self.files.sort(File.cmp_by_id)
        else:
            self.files = []

    def add_file(self, f):
        self.files.append(f)
        self.files.sort(File.cmp_by_id)

    def __eq__(self, other):
        """
        Equality test between two Dataset objects obtained from
        different locations (filesystem / db / TDS / Solr), intended
        for use in validating whether a dataset was published
        correctly.

        The mapfile_path that is optionally contained in the dataset
        is not used in the comparison: Dataset objects instantiated by
        querying published locations, rather than via
        read_filesystem.py, will probably not have this set, but this
        does not affect their validity.
        """
        return (self.name == other.name and self.version == other.version 
                and self.files == other.files)

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return """
<Dataset name %s version %s
 Files:
%s
>""" % (self.name, self.version, 
       string.join(["  " + str(f).replace("\n", "\n  ") for f in self.files],
                   "\n"))
    
    def __repr__(self):
        return "Dataset('%s', %d, files=[%s])" % (
            self.name, self.version, 
            string.join([f.__repr__() for f in self.files], ", "))
    

class File(object):

    def __init__(self, url, size, checksum, tracking_id):
        self.url = url
        self.size = int(size)
        self.checksum = checksum
        self.tracking_id = tracking_id

    def cmp_by_id(self, other):
        return cmp(self.tracking_id, other.tracking_id)

    def __eq__(self, other):
        if self.url != other.url:
            return False
        if self.size != other.size:
            return False
        if self.checksum != other.checksum:
            return False
        if self.tracking_id != other.tracking_id:
            return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return """<File: url: %s 
       size %s 
       checksum %s 
       tracking_id %s
>""" % (self.url, self.size, self.checksum, self.tracking_id)

    def __repr__(self):
        return "File('%s', %d, '%s', '%s')" % (
            self.url, self.size, self.checksum, self.tracking_id)
       

if __name__ == '__main__':

    def compare(d1, d2, expected_result):
        print "Datasets to compare:"
        print d1
        print d2
        result = (d1 == d2)
        print result
        if result != expected_result:
            raise ValueError

    cksums = ["d9b672617e2bb63948753619be1b4096",
              "6e9c8c759e9ae3edfe149874273448ca",
              "bdc065d10470efa1108f4d98650ad04e"]

    fnames = ["test1.nc", "test2.nc", "test3.nc"]

    uuids = ["0d6c7252-89ec-11e5-975b-005056b252b3", 
             "1a1ed95e-89ec-11e5-8b92-005056b252b3",
             "7547f32e-89ec-11e5-88b5-005056b252b3"]

    sizes = [1234, 5678, 12345678]

    dsnames = ["my.test.dataset.etc.etc", 
               "another.dataset.etc.etc"]

    versions = [20151010, 20151011]

    f1 = File(fnames[0], sizes[0], cksums[0], uuids[0])
    f2 = File(fnames[1], sizes[1], cksums[1], uuids[1])
    f3 = File(fnames[2], sizes[2], cksums[2], uuids[2])
    f1a = File(fnames[0], sizes[0], cksums[0], uuids[0])
    f2a = File(fnames[1], sizes[1], cksums[1], uuids[1])

    ds1 = Dataset(dsnames[0], versions[0])

    for f in (f1, f2):
        ds1.add_file(f)

    print repr(ds1)


    # matching dataset
    ds2 = Dataset(dsnames[0], versions[0])
    for f in (f2a, f1a):
        ds2.add_file(f)
    compare(ds1, ds2, True)    

    # wrong file
    ds3 = Dataset(dsnames[0], versions[0])
    for f in (f2a, f3):
        ds3.add_file(f)
    compare(ds1, ds3, False)
    
    # missing file
    ds4 = Dataset(dsnames[0], versions[0])
    ds4.add_file(f2a)
    compare(ds1, ds4, False)

    # wrong dataset ID
    ds5 = Dataset(dsnames[1], versions[0])
    for f in (f2a, f1a):
        ds5.add_file(f)
    compare(ds1, ds5, False)

    # wrong dataset version
    ds6 = Dataset(dsnames[0], versions[1])
    for f in (f2a, f1a):
        ds6.add_file(f)
    compare(ds1, ds6, False)
