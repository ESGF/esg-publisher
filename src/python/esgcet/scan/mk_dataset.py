import json
from esgcet.util.mapfile import ESGPubMapConv
from esgcet.util.settings import MAX_RECOMMENDED_FILE_COUNT, URL_Templates, VARIABLE_EXCLUDES, VARIABLE_LIMIT
import numpy as np

from urllib.parse import unquote
import esgcet.util.logger as logger

log = logger.ESGPubLogger()


class ESGPubMakeDataset:
    """
    Base class (abstract) to assemble the ESGF index records (dataset and file records).
    """

    def __init__(
        self,
        data_node,
        index_node,
        replica,
        globus,
        data_roots,
        https,
        handler_class=None,
        silent=False,
        verbose=False,
        limit_exceeded=False,
        user_project=None,
        disable_further_info=False,
        skip_opendap=False,
    ):
        """
        Constructor

        data_node (string):  ESGF Data Node to host the data
        index_node (string):  ESGF Index Node to
        replica (bool):  Is data a replca
        globus (string):  Globus endpoint UUID
        data_roots (dict): mapping of logical to file system roots for data
        https (string):  template for https urls if override, must be empty or None to use default from settings.py
        handler_class (class):  class type of the handler to construct the (format) handler object
        silent (bool):  Run in silent mode (suppress all output but errors)
        verbose (bool):  Print verbose (debug),
        limit_exceeded (bool):
        user_project (dict):  User-defined project config info
        """
        self.silent = silent
        self.verbose = verbose
        self.data_roots = data_roots
        self.globus = globus
        self.data_node = data_node
        self.index_node = index_node
        self.replica = replica
        self._https_custom = https
        self.limit_exceeded = limit_exceeded

        self.mapconv = ESGPubMapConv("")
        self.dataset = {}
        self.project = None
        self.user_project = user_project
        self.DRS = None
        self.CONST_ATTR = None
        #  The default for variables, specific projects may use "variable" instead
        self.variable_name = "variable_id"
        self.publog = log.return_logger("Make Dataset", self.silent, self.verbose)
        self.xattr = None
        self.tracking_id_set = set()
        if handler_class:
            self.handler = handler_class(self.publog)
        self._disable_further_info = disable_further_info
        self.base_path = (
            None  #  This is used to create a directory for a dataset-level Globus url
        )
        self._skip_opendap = skip_opendap

    def set_project(self, project_in):
        """
        Configure the project
        """
        self.project = project_in

    def prune_list(self, ll):
        """
        Shorten the list only actual items (no Nones)

        ll (list):  input list

        return list
        """
        for x in ll:
            if not x is None:
                yield (x)

    def load_xattr(self, xattrfn):
        """
        Load a set of "extended attributes" ie. additional key-value pairs for the dataset record from a file
        Default method, specific projects may format attributes diffeerntly
        xattrfn (string):  Full path to a .json file containing the pairs
        """
        if self.xattr:
            return
        if xattrfn:
            self.xattr = json.load(open(xattrfn))
        else:
            self.xattr = {}

    def proc_xattr(self, xattrfn):
        """
        Load and process the extended attributes
        """
        self.load_xattr(xattrfn)
        if len(self.xattr) > 0:
            tmp_xattr = self.xattr_handler()
            for key in tmp_xattr:
                self.dataset[key] = tmp_xattr[key]

    def xattr_handler(self):
        """
        Base method for handling the extended attributes
        """
        return self.xattr

    def assign_dset_values(self, master_id, version):

        self.dataset["data_node"] = self.data_node
        self.dataset["index_node"] = self.index_node
        self.dataset["master_id"] = master_id
        self.dataset["instance_id"] = f"{master_id}.v{version}"
        self.dataset["id"] = f"{self.dataset['instance_id']}|{self.dataset['data_node']}"
        if "title" in self.dataset:
            self.dataset["short_description"] = self.dataset["title"]
        self.dataset["title"] = self.dataset["master_id"]
        self.dataset["replica"] = self.replica
        self.dataset["latest"] = True
        self.dataset["type"] = "Dataset"
        self.dataset["version"] = version

        fmat_list = ["%({})s".format(x) for x in self.DRS]

        self.dataset["dataset_id_template_"] = ".".join(fmat_list)
        self.dataset["directory_format_template_"] = "%(root)s/{}/%(version)s".format(
            "/".join(fmat_list)
        )

    def format_template(self, template, root, rel):
        if self._skip_opendap and "dodsC" in template:
            return None
        if "Globus" in template:
            if self.globus != "none":
                return template.format(self.globus, root, rel)
            else:
                return None
        elif "HTTP" in template and self._https_custom:
            # Custom http template should have the hostname embedded
            return self._https_custom.format(root, rel)
        else:
            return template.format(self.data_node, root, rel)

    def gen_urls(self, proj_root, rel_path):
        res = self.prune_list(
            [
                self.format_template(template, proj_root, rel_path)
                for template in URL_Templates
            ]
        )
        return list(res)

    def parse_path(self):
        assert self.base_path
        sp = self.base_path.split("/")
        res = "/".join(sp[:-1])
        return res

    def get_file(self, mapdata, fn_trid):
        ret = self.dataset.copy()
        dataset_id = self.dataset["id"]
        ret["type"] = "File"
        fullfn = mapdata["file"]

        fparts = fullfn.split("/")
        title = fparts[-1]
        ret["id"] = "{}.{}|{}".format(ret["instance_id"], title, self.data_node)
        ret["master_id"] = f"{ret['master_id']}.{title}"

        ret["instance_id"] = "{}.{}".format(ret["instance_id"], title)
        ret["title"] = title
        ret["dataset_id"] = dataset_id
        if "tracking_id" in fn_trid:
            if fn_trid["tracking_id"] in self.tracking_id_set:
                self.publog.error(
                    f"Duplicate tracking_id {fn_trid['tracking_id']} encountered!"
                )
                exit(1)
            self.tracking_id_set.add(fn_trid["tracking_id"])
            ret["tracking_id"] = fn_trid["tracking_id"]

        for kn in mapdata:
            if kn not in ("id", "file"):
                ret[kn] = mapdata[kn]

        rel_path, proj_root = self.normalize_path(fullfn, self.data_roots)
        if not proj_root in self.data_roots:

            # Need to handle the case where the root might contain the
            # project ID, ensure that the original root and the id are
            # found.`
            root_found = False
            for root in self.data_roots:
                if self.first_val in root and proj_root in root:
                    proj_root = root
                    rel_path = rel_path.replace(f"{self.first_val}/", "")
                    root_found = True
                    if not self.base_path:
                        mapped_root = self.data_roots[root]
                        self.base_path = f"{mapped_root}/{rel_path}"

                    break

            if not root_found:
                self.publog.error(
                    "The file system root {} not found.  Please check your configuration.".format(
                        proj_root
                    )
                )
                exit(1)
        else:
            if not self.base_path:
                mapped_root = self.data_roots[proj_root]
                self.base_path = f"{mapped_root}/{rel_path}"

        ret["url"] = self.gen_urls(self.data_roots[proj_root], rel_path)
        ret["publish_path"] = f"{self.data_roots[proj_root]}/{rel_path}"
        if "number_of_files" in ret:
            ret.pop("number_of_files")
        else:
            self.publog.warning("No files present")
        if "datetime_start" in ret:
            ret.pop("datetime_start")
            ret.pop("datetime_end")

        return ret

    def update_metadata(self, record, scanobj):

        self.handler.set_bounds(record, scanobj)

    def iterate_files(self, mapdata, scandata):
        ret = []
        sz = 0
        last_file = None

        for maprec in mapdata:
            fullpath = maprec["file"]
            if fullpath not in scandata.keys():
                if (
                    not self.limit_exceeded
                    and self.project != "CREATE-IP"
                    and self.project != "cmip5"
                ):
                    self.publog.error(
                        f"Autocurator data not found for file: {fullpath}"
                    )
                    exit(1)
                continue
            scanrec = scandata[fullpath]
            file_rec = self.get_file(maprec, scanrec)
            file_rec["url"] = [unquote(x) for x in file_rec["url"] if x]
            last_file = file_rec
            sz += file_rec["size"]
            ret.append(file_rec)

        access = [x.split("|")[2] for x in last_file["url"]]

        return ret, sz, access

    def get_records(self, mapdata, scanobj, xattrfn=None, user_project=None):

        self.user_project = user_project
        self.load_xattr(xattrfn)

        if isinstance(mapdata, str):
            mapobj = json.load(open(mapdata))
        else:
            mapobj = mapdata

        attrs = self.handler.get_attrs_dict(scanobj)

        # Check against recommended maximum file count
        file_count = len(mapobj)
        if file_count > MAX_RECOMMENDED_FILE_COUNT:
            self.publog.warning(
                f"Dataset contains {file_count} files, which exceeds the "
                f"recommended maximum of {MAX_RECOMMENDED_FILE_COUNT}. "
                f"Large file counts may exceed event payload size limits and backend "
                f"record size constraints. Consider aggregating files or splitting the dataset."
            )

        #self.mapconv.set_map_arr(mapobj)
        #mapdict = self.mapconv.parse_map_arr()

        # self.publog.debug('Mapfile dictionary:\n' + json.dumps(mapdict, indent=1)) # Superverbose

        #scandict = self.handler.get_scanfile_dict(scanobj, mapdict)
        # self.publog.debug('Autocurator Scanfile dictionary:\n' + json.dumps(scandict, indent=1))  # Superverbose

        ret, sz, access = self.iterate_files(mapdict, scandict)
        self.dataset["size"] = sz
        self.dataset["access"] = access

        self.proc_xattr(xattrfn)

        ret.append(self.dataset)
        return ret

    @staticmethod
    def normalize_path(path, data_roots):

        proj_root = None

        # Check each data root to see if it matches the provided path
        for data_root, _ in data_roots.items():
            path_match = "{}/".format(data_root.rstrip("/"))
            if path.startswith(path_match):

                rel_path = path[len(path_match) :]
                proj_root = data_root.rstrip("/")

        if not proj_root:
            raise (BaseException("File Path does not match any data roots!"))

        return rel_path, proj_root
