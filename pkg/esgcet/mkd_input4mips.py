from esgcet.mk_dataset import ESGPubMakeDataset
from esgcet.settings import GA, GA_DELIMITED

class ESGPubMKDinput4MIPs(ESGPubMakeDataset):

    def xattr_handler(self):
        return [x for x in self.xattr.values()][0]

    def global_attributes(self, projkey, scandata):
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
                if facetkey in GA_DELIMITED[projkey]:
                    delimiter = GA_DELIMITED[projkey][facetkey]
                    self.dataset[facetkey] = facetval.split(delimiter)
                else:
                    self.dataset[facetkey] = facetval

    def proc_xattr(self, xattrfn):
        pass

    def get_records(self, mapdata, scanfilename, xattrfn=None, user_project=None):

        self.load_xattr(xattrfn)
        return super().get_records(mapdata, scanfilename)
