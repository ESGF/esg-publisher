class PublicationLevels(object):

    disk = "disk"
    db = "db"
    tds = "tds"
    solr = "solr"

    @staticmethod
    def all():
        "Return a tuple of the publication levels in order."
        pl = PublicationLevels
        return (pl.disk, pl.db, pl.tds, pl.solr)

class ESGFPublicationVerificationError(Exception): pass

class ESGFPublicationTestError(Exception): pass