from esgcet.mk_dataset import ESGPubMakeDataset

class ESGPubMKDinput4MIPs(ESGPubMakeDataset):

    def xattr_handler(self, in_xattr):
        return [x for x in in_xattr.values()][0]
