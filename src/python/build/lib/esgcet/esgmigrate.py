from ESGConfigParser import SectionParser
import configparser as cfg
import os, sys
from urllib.parse import urlparse
import shutil
from datetime import date
from pathlib import Path
import json
import esgcet.logger as logger
import yaml
import traceback

log = logger.ESGPubLogger()

DEFAULT_ESGINI = '/esg/config/esgcet/'
CONFIG_FN_DEST = "~/.esg/esg.yaml"

# These are the keys that 
MIGRATE_KEYS = ['pid_creds', 'data_roots', 'user_project_config']

def project_list(cfg_obj):
    return [x[0] for x in cfg_obj.get_options_from_table('project_options')]

class ESGPubMigrate(object):

    def __init__(self, i, newpath, silent=False, verbose=False):
        self.ini_path = i
        self.silent = silent
        self.verbose = verbose
        self.save_path = newpath
        self.publog = log.return_logger('esgmigrate', silent, verbose)

    def migrate_new(self):

        config = cfg.ConfigParser()
        ini_file = self.ini_path
        if os.path.isdir(ini_file):
            ini_file = os.path.join(ini_file, 'esg.ini')
        config.read(ini_file)        
        cf_user = config['user']

        cf_dict = {}
        for key in cf_user:
            if key in MIGRATE_KEYS:
                cf_val =  cf_user[key]
                if type(cf_val) is str and len(cf_val) > 1:
                    try:
                        print(cf_val)
                        cf_json = json.loads(cf_user[key])
                        cf_dict[key] = cf_json
                    except BaseException as ex:
                        self.publog.warn(f"Expected JSON string for {key} could not be parsed")
                        traceback.print_exc()
                else:
                    self.publog.warn(f"{key} expected in JSON format, has {cf_val}")
            else:
                cf_dict[key] = cf_user[key]
        del cf_dict['note']
        self.write_config(cf_dict)

    def project_migrate(self, project):

        if not project:
            return None
        path = self.ini_path
        SP = SectionParser("project:{}".format(project), directory=path)
        SP.parse(path)

        ret = {'DRS' : SP.get_facets('dataset_id')}
        try:
            ret['CONST_ATTR'] = { x[0] : x[1] for x in SP.get_options_from_table('category_defaults') }
        except:
            ret['CONST_ATTR'] = {}
            self.publog.debug("No category defaults found for {}".format(project))
        return ret


    def migrate(self, project=None):

        if not os.path.exists(os.path.join(self.ini_path, "esg.ini")):
            self.publog.error("Old config " + self.ini_path + "esg.ini not found or unreadable.")
            exit(1)

        try:
            sp = SectionParser('config:cmip6')
            sp.parse(self.ini_path)
        except Exception as e:
            self.publog.exception("Exception encountered.")
            return

        thredds_url = sp.get("thredds_url")
        res = urlparse(thredds_url)
        data_node = res.netloc


        index_node =''
        if 'rest_service_url' in sp:
            index_url = sp.get('rest_service_url')
            res = urlparse(index_url)
            index_node = res.netloc
        else:
            self.publog.warning("No REST publishing url found in old config, will need to set index_node setting")
        
        try:
            cmor_path = sp.get('cmor_table_path')
        except:
            cmor_path = "/usr/local/cmip6-cmor-tables/Tables"

        
        try:
            cmor_path = sp.get('cmor_table_path')
        except:
            cmor_path = "/usr/local/cmip6-cmor-tables/Tables"

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

        DATA_TRANSFER_NODE = None
        GLOBUS_UUID = None

        for line in svc_urls:
            if line[0] == "GridFTP":
                res = urlparse(line[1])
                DATA_TRANSFER_NODE = res.netloc
            elif line[0] == "Globus":
                parts= line[1].split(':')
                GLOBUS_UUID = parts[1][0:36] # length of UUID

        cert_base = 'none'
        if 'heshessian_service_certfile' in sp:
            cert_base = sp.get('hessian_service_certfile')
        
        CERT_FN = cert_base.replace('%(home)s', '~')

        self.publog.debug(str(dr_dict))
        self.publog.debug(str(pid_creds))
        self.publog.debug(data_node)
        self.publog.debug(index_node)
        self.publog.debug(CERT_FN)
        self.publog.debug(DATA_TRANSFER_NODE)
        self.publog.debug(GLOBUS_UUID)
        self.publog.debug(project)

        project_config = {project: self.project_migrate(project)}
        new_config = {"data_node": data_node, "index_node": index_node, "data_roots": dr_dict, "cert": CERT_FN,
                      "globus_uuid": GLOBUS_UUID, "data_transfer_node": DATA_TRANSFER_NODE, "pid_creds": pid_creds,
                      "cmor_path" : cmor_path }
        if project_config:
            new_config["project_cfg"] = project_config
        self.write_config(new_config)

    def write_config(self, new_config):

        pid_creds = new_config['pid_creds']
        new_creds = {}
        for it in pid_creds:
            url = it['url']
            del it['url']
            new_creds[url] = it
        new_config['pid_creds'] = new_creds

        d = date.today()
        t = d.strftime("%y%m%d")
        config_file = self.save_path
        if os.path.exists(self.save_path):
            backup = f"{self.save_path}.{t}.bak"
            shutil.copyfile(config_file, backup)

        with open(config_file, 'w') as f:
            yaml.dump(new_config, f)
