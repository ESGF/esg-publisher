import ConfigParser
import os

config = None

def parse_test_config():
    top_dir = os.path.realpath(os.path.curdir)
    #top_dir = os.path.split(os.path.realpath(os.path.curdir))[0]
    conf = ConfigParser.ConfigParser()
    conf.read(os.path.join(top_dir, "test_suite.ini"))

    d = {}
    for item in conf.defaults():
        d[item] = conf.get("DEFAULT", item)

    return d

if not config:
    config = parse_test_config()
