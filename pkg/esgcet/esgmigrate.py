from ESGConfigParser import SectionParser
import configparser as cfg
import os, sys
from urllib.parse import urlparse
import settings
import shutil
from datetime import date
from pathlib import Path

DEFAULT_ESGINI = '/esg/config/esgcet'


def run(args):

    ini_path = DEFAULT_ESGINI

    if 'fn' in args:
        ini_path = args['fn']

    #  TODO  For automigrate, exit if the new settings file is found

    if not os.path.exists(ini_path + '/esg.ini'):
        print("esg.ini not found or unreadable")
        return

    try:
        sp = SectionParser('config:cmip6')
        sp.parse( ini_path)
    except Exception as e:
        print("Exception encountered {}".format(str(e)))
        return

    thredds_url = sp.get("thredds_url")
    res = urlparse(thredds_url)
    data_node = res.netloc

    index_url = sp.get('rest_service_url')
    res = urlparse(index_url)
    index_node = res.netloc

    log_level = sp.get('log_level')

    try:
        pid_creds_in = sp.get_options_from_table('pid_credentials')
    except:
        pid_creds_in = []

    pid_creds = []
    for i, pc in enumerate(pid_creds_in):
        rec = {}
        rec['url'] = pc[0]
        rec['port'] = pc[1]
        rec['vhost'] = pc[2]
        rec['user'] = pc[3]
        rec['password'] = pc[4]
        rec['ssl_enabled'] = bool(pc[5])
        rec['priority'] = i+1
        pid_creds.append(rec)

    try:
        data_roots = sp.get_options_from_table('thredds_dataset_roots')
    except:
        data_roots = []

    dr_dict = {}
    for dr in data_roots:
        dr_dict[dr[1]] = dr[0]

    try:
        svc_urls = sp.get_options_from_table('thredds_file_services')
    except:
        svc_urls = []

    DATA_TRANSFER_NODE = ""
    GLOBUS_UUID = ""

    for line in svc_urls:
        if line[0] == "GridFTP":
            res = urlparse(line[1])
            DATA_TRANSFER_NODE = res.netloc
        elif line[0] == "Globus":
            parts= line[1].split(':')
            GLOBUS_UUID = parts[1][0:36] # length of UUID

    cert_base = sp.get('hessian_service_certfile')

    CERT_FN = cert_base.replace('%(home)s', '~')

    d = date.today()
    t = d.strftime("%y%m%d")
    home = str(Path.home())
    config_file = home + "/.esg/esg.ini"
    backup = home + "/.esg/" + t + "esg.ini"
    shutil.copyfile(config_file, backup)
    config = cfg.ConfigParser()
    config.read(config_file)
    new_config = {"data_node": data_node, "index_node": index_node, "data_roots": json.dumps(dr_dict), "cert": CERT_FN,
                  "globus_uuid": GLOBUS_UUID, "data_transfer_node": DATA_TRANSFER_NODE, "pid_creds": json.dumps(pid_creds)}
    for key, value in new_config.items():
        try:
            test = config['user'][key]
        except:
            config['user'][key] = value
    with open(config_file, "w") as cf:
        config.write(cf)


def main():

    args = {}
    args['fn'] = sys.argv[1]
    run(args)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
