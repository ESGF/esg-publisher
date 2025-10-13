from esgcet.pub_client import publisherClient
import esgcet.logger as logger
import os


from esgcet.globus_search import GlobusSearchIngest

log = logger.ESGPubLogger()


class ESGPubIndex:
    """
    Wrapper class for push-publishing of records to the index node.
    """
    def __init__(self, index_node="", UUID=None,  verbose=False, silent=False, verify=True, auth=None, arch_cfg=None, file_cache=None, dry_run=False):
        """
        Constructor, creates a "client" object
        """
        self.silent = silent
        self.verbose = verbose
        if index_node:
            self.pubCli = publisherClient("", index_node, verify=verify, verbose=self.verbose, silent=self.silent, auth=auth)
        else:
            self._index_UUID = UUID
        self.publog = log.return_logger('Index Publication', silent, verbose)
        self.arch_cfg = arch_cfg

        
        self._cache_dir = file_cache
        self._dry_run = dry_run

    def do_globus(self, d):
        gs = GlobusSearchIngest(d, self._cache_dir)
        res = gs.run(False)
        if not self._dry_run:
            gs.extern_globus_publish(res, self._index_UUID)
        else:
            self.publog.info(f"dry run on, not publishing {res}")
#        os.system(f"globus search ingest {self._index_UUID} {res}")

    def gen_xml(self, d):
        out = []
        out.append("<doc>\n")

        for key in d:

            val = d[key]
            if key == "description":
                val = ' '.join(val)
                out.append('  <field name="{}">{}</field>\n'.format(key, val))
            elif type(val) is list:
                for vv in val:
                    out.append('  <field name="{}">{}</field>\n'.format(key, vv))
            else:
                out.append('  <field name="{}">{}</field>\n'.format(key, val))
        out.append("</doc>\n")
        return ''.join(out)

    def do_publish(self, dataset):
        """ handle dataset publishing
        dataset (list) of dictionary records
        """
        rc = True
        for rec in dataset:

            new_xml = self.gen_xml(rec)

            if self.arch_cfg:
                resp = self.archive_rec(rec, new_xml)
                if not resp:
                    self.publog.error("Error in archiving.  Archiving haulting.  Publication will continue")
                    self.arch_cfg = None
                    rc = False
            self.publog.debug(new_xml)
            self.pubCli.publish(new_xml)
        return rc

    def pub_xml(self, doc):
        self.pubCli.publish(doc)

    def archive_rec(self, rec, new_xml):

        if "dataset_id" in rec:
            id_key = "dataset_id"
        else:
            id_key = "id"
        pathid = rec[id_key]
        pathid = pathid[:pathid.find('|')]
        dsparts = pathid.split('.')
        fname = rec["id"] + ".xml"

        pathlen = self.arch_cfg["length"] 
        if pathlen  > len(dsparts):
            pathlen = len(dsparts)
        subpath = '/'.join(dsparts[0:pathlen])


        destpath = os.path.join(self.arch_cfg["archive_path"], subpath)
        try:
            res = os.system(f"mkdir -p {destpath}")
            if not res == 0:
                raise RuntimeError(f"{destpath} {res} (possible permission error?)")
        except Exception as ex:
            self.publog.exception(f"Error creating archive directory {ex}")
            exit(1)
        try:
            with open(os.path.join(destpath, fname), "w") as outf:
                outf.write(new_xml)
        except Exception as ex:
            self.publog.exception(f"Error writing xml file to archive. {ex}")
            return False
        return True
