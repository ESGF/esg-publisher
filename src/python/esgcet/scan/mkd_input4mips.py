from esgcet.mk_dataset import ESGPubMakeDataset
from esgcet.settings import GA, GA_DELIMITED
import esgcet.logger as logger

log = logger.ESGPubLogger()


class ESGPubMKDinput4MIPs(ESGPubMakeDataset):

    def __init__(self, data_node, index_node, replica, globus, data_roots, dtn, silent=False, verbose=False, limit_exceeded=False, user_project=None, skip_opendap=False):
        super().__init__(data_node, index_node, replica, globus, data_roots, dtn, silent, verbose, limit_exceeded, user_project, skip_opendap=skip_opendap)
        self.publog = log.return_logger('Make Dataset input4MIPs', silent, verbose)

    def xattr_handler(self):
        if not self.xattr:
            return {}
        if len(self.xattr) < 1:
            return {}
        return [x for x in self.xattr.values()][0]

    def global_attributes(self, proj, scandata):
        projkey = proj.lower()
        # handle Global attributes if defined for the project
        handler = self.xattr_handler()
        if projkey in GA:
            for facetkey in GA[projkey]:
                # did we find a GA in the data by the the key name

                if facetkey in handler:
                    facetval = handler[facetkey]
                elif facetkey in scandata:
                    facetval = scandata[facetkey]
                    # is this a delimited attribute ?
                self.dataset[facetkey] = facetval

    def proc_xattr(self, xattrfn):
        pass

    def get_records(self, mapdata, scanfilename, xattrfn=None, user_project=None):

        self.load_xattr(xattrfn)
        return super().get_records(mapdata, scanfilename)
