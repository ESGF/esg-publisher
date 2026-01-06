from abc import ABC, abstractmethod
import esgcet.logger as logger

log = logger.ESGPubLogger()


class ESGUpdateBase(ABC):


    def __init__(self, silent=False, verbose=False):
        self.publog = log.return_logger('Update Record', silent, verbose)

    @abstractmethod
    def update_file(self, dsetid : str):
        pass

    @abstractmethod
    def update_dataset(self, dsetid : str):
        pass

    @abstractmethod
    def query_update(self, data_node : str, master_id : str):
        pass

    def run(self, input_rec : dict):
        """ Check a record in the index and peform the updates

            input_rec - a json record to be published containing a "master_id" and "data_node" fields with 
                        a new version
        """
    # The dataset record either first or last in the input file
        dset_idx = -1
        if not input_rec[dset_idx]['type'] == 'Dataset':
            dset_idx = 0

        if not input_rec[dset_idx]['type'] == 'Dataset':
            self.publog.error("Could not find the Dataset record.  Malformed input, exiting!")
            exit(1)

        mst = input_rec[dset_idx]['master_id']
        dnode = input_rec[dset_idx]['data_node']

        dsetid = self.query_update(dnode, mst)

        if dsetid:
            self.update_dataset(dsetid)
            self.update_file(dsetid)
            self.publog.info('Found previous version, updating the record: {}'.format(dsetid))

        else:
            version = input_rec[dset_idx]['version']
            self.publog.info('First dataset version for {}: v{}.)'.format(mst, version))

