import os
import xml.etree.ElementTree as ET

from publication_objects import Dataset, File
import urlopen

class NotFound(Exception):
    pass


class ReadThredds(object):

    def __init__(self, esg_conf, conf=None):

        # esg_conf is the esg.ini interface, used for the THREDDS paths

        # conf is the test suite config, optionally used to tell the URL
        # opener where to find SSL host keys
        
        self.local_root = esg_conf.get_thredds_root()
        self.url_root = esg_conf.get_thredds_url_root()
        self.conf = conf

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
        catalog = self._path_to_catalog(path)

        dsets = map(self._parse_dataset,
                    self._get_children_by_tag(catalog, "dataset"))
        if return_list:
            return dsets
        else:
            assert(len(dsets) == 1)
            return dsets[0]

    def _path_to_catalog(self, path):
        if path.startswith("http://") or path.startswith("https://"):
            try:
                fh = urlopen.urlopen(path, self.conf)
            except urlopen.HTTPError:
                raise NotFound
            tree = ET.parse(fh)
            fh.close()
        else:
            try:
                fh = open(path)
            except IOError:
                raise NotFound
            tree = ET.parse(fh)
            fh.close()
        root = tree.getroot()
        assert(root.tag.endswith("}catalog"))
        return root
        
    def _get_children_by_tag(self, el, name):
        chs = []
        for ch in el.getchildren():
            if ch.tag.endswith("}" + name):
                chs.append(ch)
        return chs

    def _parse_dataset(self, el):
        """
        Parse a single top-level dataset element.  Return Dataset object.
        """
        # top "dataset" element should be the dataset
        properties = self._get_properties(el)
        version = properties["dataset_version"]
        name = properties["dataset_id"]
        ds = Dataset(name, version)
        # child "dataset" elements may be files or aggregations
        for ch in self._get_children_by_tag(el, "dataset"):
            props = self._get_properties(ch)
            if "file_id" in props:
                url = ch.get("urlPath")
                tracking_id = props["tracking_id"]
                checksum = props["checksum"]
                size = props["size"]
                ds.add_file(File(url, size, checksum, tracking_id))
        return ds

    def _get_properties(self, el):
        props = {}
        for ch in self._get_children_by_tag(el, "property"):
            props[ch.get('name')] = ch.get('value')
        return props

    def get_catalog_location(self, dsid, path):
        """
        get location of an individual catalog by looking it up in the 
        specified top-level catalog
        """
        catalog = self._path_to_catalog(path)
        for ch in self._get_children_by_tag(catalog, "catalogRef"):
            if ch.get("name") == dsid:
                for key in ch.keys():
                    if key.endswith("}href"):
                        return ch.get(key)
                else:
                    raise ValueError("'href' link missing in catalogRef")

        raise NotFound


    def get_catalog_location_via_local(self, dsid):
        """
        get location of an individual catalog by looking it up in the 
        top-level catalog on the local filesystem
        """
        return self.get_catalog_location(dsid,
                                         self.local_path("catalog.xml"))

    def get_catalog_location_via_http(self, dsid):
        """
        get location of an individual catalog by looking it up in the 
        top-level catalog served by the THREDDS webapp
        """
        return self.get_catalog_location(dsid,
                                         self.url_path("catalog.xml"))
        


if __name__ == '__main__':

    import esg_config

    conf = esg_config.Config()
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

    id = ds_served.id
    assert catalog == rt.get_catalog_location_via_local(id)
    assert catalog == rt.get_catalog_location_via_http(id)

    try:
        rt.get_catalog_location_via_http("blah")
    except NotFound:
        pass
    else:
        raise Exception("blah should not have been found")
