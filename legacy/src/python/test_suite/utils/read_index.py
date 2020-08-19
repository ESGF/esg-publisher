import json
import re

import urlopen


from publication_objects import Dataset, File

class NotFound(Exception):
    pass

class ReadIndex(object):
    
    def __init__(self, esg_conf, conf=None):
        index_node = esg_conf.get_index_node()
        data_node = esg_conf.get_data_node()

        self.url_format = "https://%s/search_files/%%s.v%%d|%s/%s/" % (
            index_node, data_node, index_node)

        self.conf = conf

    def get_dset(self, dataset_id, version):
        """
        returns a Dataset object corresponding to the requested ID
        """
        query_url = self.url_format % (dataset_id, version)        
        response = urlopen.urlopen(query_url, self.conf)
        js = json.load(response)

        assert js.has_key("responseHeader")

        results = js["response"]
        files = results["docs"]
        if not files:
            raise NotFound

        ds = Dataset(dataset_id, version)

        for f in files:
            ds.add_file(File(self.extract_urlpath(f["url"]),
                             f["size"],
                             self.only_value(f["checksum"]),
                             self.only_value(f["tracking_id"])))

        return ds

    
    _urlpath_match = re.compile("thredds/fileServer/(.*?)\|").search
        
    def extract_urlpath(self, full_urls):
        """
        from the list of full urls returned by search, 
        return the 'url' comparable to what THREDDS calls the 'urlPath'
        
        e.g. if full URL starts
        http://the.host.name/thredds/fileServer/esg_dataroot/cmip5/...
        The bit of interest starts   esg_dataroot/cmip5/...

        On input list, the various URLs will be the different access methods.
        Assume that one of them is a fileServer URL like above
        """
        for url in full_urls:
            m = self._urlpath_match(url)
            if m:
                return m.group(1)
        raise ValueError

    def only_value(self, list):
        assert len(list) == 1
        return list[0]


if __name__ == '__main__':
    import read_esg_config

    name = 'cmip5.output1.CSIRO-QCCCE.CSIRO-Mk3-6-0.historical.mon.land.Lmon.r5i1p1'
    version = 1

    conf = read_esg_config.Config()
    ri = ReadIndex(conf)
    ds = ri.get_dset(name, version)
    print ds
