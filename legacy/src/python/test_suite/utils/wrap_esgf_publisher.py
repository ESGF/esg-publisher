import string
import subprocess as sp

from datasets import all_datasets
import verify

class PublishFuncs(object):

    def __init__(self, logger=None):
        if logger == None:
            logger = logging.getLogger()
        self.logger = logger
        self.verifier = verify.VerifyFuncs(logger)

    def publish(self, ds):
        self.logger.debug("doing publish: %s" % ds.id)
        self.publish_to_db(ds)
        self.publish_to_tds(ds)
        self.publish_to_solr(ds)
        self.logger.debug("done publish: %s" % ds.id)

    def publish_to_db(self, ds):
        self.logger.debug("doing publish_to_db: %s" % ds.id)
        self.run_command("esgpublish",
                         "--project", ds.id.split(".")[0],
                         "--new-version", str(ds.version),
                         "--map", ds.mapfile_path)
        self.logger.debug("done publish_to_db: %s" % ds.id)

    def publish_to_tds(self, ds, thredds_reinit=True):
        self.logger.debug("doing publish_to_tds: %s" % ds.id)
        command = ["esgpublish", 
                   "--project", ds.id.split(".")[0],
                   "--new-version", str(ds.version),
                   "--noscan",
                   "--thredds",
                   "--service", "fileservice",
                   "--use-existing", self.format_name(ds)]
        if not thredds_reinit:
            command.append("--no-thredds-reinit")
        self.run_command(*command)
        self.logger.debug("done publish_to_tds: %s" % ds.id)

    def publish_to_solr(self, ds):
        self.logger.debug("doing publish_to_solr: %s" % ds.id)
        self.run_command("esgpublish", 
                         "--project", ds.id.split(".")[0],
                         "--new-version", str(ds.version),
                         "--noscan",
                         "--publish",
                         "--use-existing", self.format_name(ds))
        self.logger.debug("done publish_to_solr: %s" % ds.id)

    def unpublish(self, ds):
        self.logger.debug("doing unpublish: %s" % ds.id)
        try:
            # this check is just to save time doing an unnecessary
            # (slowish) unpublish, rather than to verify success of a
            # previous unpublish, so do not retry if it seems to be
            # published (in fact retry=False is now the default anyway)
            self.verifier.verify_unpublished_from_solr(ds, retry=False)
        except:
            self.unpublish_from_solr(ds)
        try:
            self.verifier.verify_unpublished_from_tds(ds)
        except:
            self.unpublish_from_tds(ds)
        try:
            self.verifier.verify_unpublished_from_db(ds)
        except:
            self.unpublish_from_db(ds)
        self.logger.debug("done unpublish: %s" % ds.id)

    def unpublish_from_db(self, ds):
        self.logger.debug("doing unpublish_from_db: %s" % ds.id)
        self.run_command("esgunpublish",
                         "--database-only",
                         "--no-republish",
                         self.format_name(ds))
        self.logger.debug("done unpublish_from_db: %s" % ds.id)

    def unpublish_from_tds(self, ds):
        self.logger.debug("doing unpublish_from_tds: %s" % ds.id)
        self.run_command("esgunpublish",
                         "--skip-index",
                         "--no-republish",
                         self.format_name(ds))
        self.logger.debug("done unpublish_from_tds: %s" % ds.id)

    def unpublish_from_tds_multi(self, dsets):
        self.logger.debug("doing unpublish_from_tds: %s" % [ds.id for ds in dsets])
        cmd_in = ""
        for ds in dsets:
            cmd_in += self.format_name(ds) + "\n"
        self.run_command("esgunpublish",
                         "--skip-index",
                         "--no-republish",
                         "--use-list", "-",
                         data_in = cmd_in)
        self.logger.debug("done unpublish_from_tds: %s" % ds.id)

    def unpublish_from_solr(self, ds):
        self.logger.debug("doing unpublish_from_solr: %s" % ds.id)
        self.run_command("esgunpublish",
                         "--skip-thredds",
                         "--no-republish",
                         self.format_name(ds))
        self.logger.debug("done unpublish_from_solr: %s" % ds.id)

    def delete_all(self, dset_list = None):
        if dset_list == None:
            dset_list = all_datasets
        self.logger.debug("doing delete_all")
        for ds in dset_list:
            self.unpublish(ds)
        self.logger.debug("done delete_all")

    def format_name(self, ds):
        return "%s#%s" % (ds.name, ds.version)

    def run_command(self, *command, **kwargs):
        try:
            data_in = kwargs['data_in']
        except KeyError:
            data_in = None
        self.logger.debug("running command: %s" % string.join(command, " "))
        proc = sp.Popen(command, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        data = proc.communicate(data_in)
        output = data[0] + data[1]  # stdout, stderr
        status = proc.returncode
        #
        # If it appears to fail, do not give an exception (instead, rely on
        # the publication tests to detect that it did not work), but do warn.
        #
        if status != 0:
            self.logger.warn("exit status of %s command was %s" % 
                             (command[0], status))
            self.logger.warn("output was:\n %s\n------" % output)
        else:
            self.logger.debug("output of successful command:\n %s\n------" % output)
        return status
