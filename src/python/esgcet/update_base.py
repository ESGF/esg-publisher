from abc import ABC, abstractmethod

class ESGUpdateBase:


    def __init__(self):
        pass

    @abstractmethod
    def update_file(self, dsetid : str):
        pass

    @abstractmethod
    def update_dataset(self, dsetid : str):
        pass

    @abstractmethod
    def query_update(self):
        pass

    def run(self, input_rec):
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
            self.update_core(dsetid,"datasets")
            self.update_core(dsetid, "files")
            self.publog.info('Found previous version, updating the record: {}'.format(dsetid))

        else:
            version = input_rec[dset_idx]['version']
            self.publog.info('First dataset version for {}: v{}.)'.format(mst, version))

