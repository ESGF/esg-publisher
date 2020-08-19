import re
import os
import ConfigParser


class Config(object):

    def __init__(self, filename = "test_suite.ini"):
        self.top_dir = self._get_top_dir()
        self.d = self._parse_test_config(filename)
        self.devel_options_used = set()
        
    def _get_top_dir(self):
        p = os.path
        return p.realpath(p.join(p.dirname(__file__), ".."))

    _var_re = re.compile("\$\{([a-zA-Z0-9_]+)\}")

    def _parse_test_config(self, filename):
        """
        Parse config file into dictionary, after pre-setting the "topdir" entry
        """
        conf = ConfigParser.SafeConfigParser()        
        conf.set("DEFAULT", "topdir", self.top_dir)
        conf.read(os.path.join(self.top_dir, filename))
        return dict(conf.items("DEFAULT"))

    def get(self, key):
        """
        Get a config variable.  Raise exception if not found.
        """
        return self.d[key]

    def get_with_default(self, key, default):
        """
        Get a config variable.  Returns default value if not found.
        """
        try:
            return self.d[key]
        except KeyError:
            return default

    _true_vals = (True, 1, 'True', 'true', 'on')
    _false_vals = (False, 0, 'False', 'false', 'off')

    def is_set(self, key, default=False):
        value = self.get_with_default(key, default)
        if value in self._true_vals:
            if key.startswith("devel_"):
                self.devel_options_used.add(key)
            return True
        if value in self._false_vals:
            return False
        raise ValueError("non-boolean value for '%s'" % key)
        

config = Config()

