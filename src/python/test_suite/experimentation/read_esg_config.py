import re

from ConfigParser import ConfigParser

"""
Class to read the relevant parts of esg.ini
"""


class Config(object):
    
    def __init__(self, path = '/esg/config/esgcet/esg.ini'):
        self.path = path
        self.cp = ConfigParser()
        assert self.cp.read(path)

    _re_keyval = re.compile('(.*)\s+\|\s+(.*?)\s*$')
    def get_dataset_roots(self):
        """
        Return dataset roots as list of (key, path) tuples
        (path to end with exactly one /)
        """
        roots = []
        for line in self.cp.get("DEFAULT", "thredds_dataset_roots").split("\n"):
            m = self._re_keyval.match(line)
            if m:
                key = m.group(1)
                dirpath = m.group(2)
                while dirpath.endswith("/"):
                    dirpath = dirpath[:-1]
                roots.append((key, dirpath + "/"))
        return roots

    def get_thredds_root(self):
        return self.cp.get("DEFAULT", "thredds_root")

    def get_thredds_url_root(self):
        return self.cp.get("DEFAULT", "thredds_url")
        
    def get_db_url(self):
        return self.cp.get("DEFAULT", "dburl")

if __name__ == '__main__':
    conf = Config()
    print conf.get_dataset_roots()
    
