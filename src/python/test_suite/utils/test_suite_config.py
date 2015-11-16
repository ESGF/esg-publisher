import re
import os
import ConfigParser


class Config(object):

    def __init__(self, filename = "test_suite.ini"):
        self.top_dir = self._get_top_dir()
        self.d = self._parse_test_config(filename)
        
    def _get_top_dir(self):
        p = os.path
        return p.realpath(p.join(p.dirname(__file__), ".."))

    _var_re = re.compile("\$\{([a-zA-Z0-9_]+)\}")

    def _parse_test_config(self, filename):
        """
        Parse config file into dictionary and do variable substitutions
        """
        conf = ConfigParser.ConfigParser()
        conf.read(os.path.join(self.top_dir, filename))

        d = {}
        for item in conf.defaults():
            value = conf.get("DEFAULT", item)
            while True:
                m = self._var_re.search(value)
                if not m:
                    break
                varname = m.group(1)
                if varname == 'topdir':
                    subs_value = self.top_dir
                else:
                    try:
                        subs_value = d[varname]
                    except IndexError:
                        raise Exception("substitution ${%s} failed in '%s' in %s" %
                                        (varname, item, filename))
                value = value[ : m.start()] + subs_value + value[m.end() : ]
            d[item] = value
        return d

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
            return True
        if value in self._false_vals:
            return False
        raise ValueError("non-boolean value for '%s'" % key)
        

config = Config()

