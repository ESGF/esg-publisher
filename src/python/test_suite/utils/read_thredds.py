import urllib2
import os
import xml.etree.ElementTree as ET

from publication_objects import Dataset, File


class NotFound(Exception):
    pass


class ReadThredds(object):

    def __init__(self, conf):

        self.local_root = conf.get_thredds_root()
        self.url_root = conf.get_thredds_url_root()

    def local_path(self, catalog_location):
        return os.path.join(self.local_root, catalog_location)

    def url_path(self, catalog_location):
        return os.path.join(self.url_root, catalog_location)
        
    def parse_catalog(self, path, return_list = False):
        """
        Parse THREDDS catalogue, which may be a local XML file or a URL
        path from the server.

        Expect to find one dataset and return it, but if return_list=True then 
        instead return list of datasets.

        Raises NotFound if it isn't there.
        """
        if path.startswith("http://") or path.startswith("https://"):
            try:
                fh = urllib2.urlopen(path)
            except urllib2.HTTPError:
                raise NotFound
            tree = ET.parse(fh)
        else:
            try:
                fh = open(path)
            except IOError:
                raise NotFound
            tree = ET.parse(fh)
        dsets = self.parse_tree(tree)
        fh.close()
        if return_list:
            return dsets
        else:
            assert(len(dsets) == 1)
            return dsets[0]

    def parse_tree(self, tree):
        root = tree.getroot()
        assert(root.tag.endswith("}catalog"))

        return map(self.parse_dataset,
                   self.get_children_by_tag(root, "dataset"))

    def get_children_by_tag(self, el, name):
        chs = []
        for ch in el.getchildren():
            if ch.tag.endswith("}" + name):
                chs.append(ch)
        return chs

    def parse_dataset(self, el):
        """
        Parse a single top-level dataset element.  Return Dataset object.
        """
        # top "dataset" element should be the dataset
        properties = self.get_properties(el)
        version = properties["dataset_version"]
        name = properties["dataset_id"]
        ds = Dataset(name, version)
        # child "dataset" elements may be files or aggregations
        for ch in self.get_children_by_tag(el, "dataset"):
            props = self.get_properties(ch)
            if "file_id" in props:
                url = ch.get("urlPath")
                tracking_id = props["tracking_id"]
                checksum = props["checksum"]
                size = props["size"]
                ds.add_file(File(url, size, checksum, tracking_id))
        return ds

    def get_properties(self, el):
        props = {}
        for ch in self.get_children_by_tag(el, "property"):
            items = dict(ch.items())
            props[items['name']] = items['value']
        return props



if __name__ == '__main__':

    import read_esg_config

    conf = read_esg_config.Config()
    rt = ReadThredds(conf)
    catalog = "30/cmip5.output1.CSIRO-QCCCE.CSIRO-Mk3-6-0.historical.mon.land.Lmon.r5i1p1.v1.xml"

    url_path = rt.url_path(catalog)
    local_path = rt.local_path(catalog)

    print url_path
    print local_path

    ds_served = rt.parse_catalog(url_path)
    ds_local = rt.parse_catalog(local_path)

    print "Dataset as read locally", ds_local
    print "Dataset as read from server", ds_served

    assert ds_local == ds_served

