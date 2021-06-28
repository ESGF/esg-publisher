from esgcet.pub_client import publisherClient
import esgcet.logger as logger

log = logger.Logger()
publog = log.return_logger('Index Publication')


class ESGPubIndex:

    def __init__(self, hostname, cert_fn, verbose=False, silent=False, verify=False, auth=True):
        self.silent = silent
        self.verbose = verbose
        self.pubCli = publisherClient(cert_fn, hostname, verify=verify, verbose=self.verbose, silent=self.silent, auth=auth)

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

        for rec in dataset:

            new_xml = self.gen_xml(rec)
            if self.verbose:
                publog.info(new_xml)
            self.pubCli.publish(new_xml)

