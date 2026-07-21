import json
from datetime import datetime
import traceback
import esgcet.logger as logger

log = logger.ESGPubLogger()

class ESGPubMapConv:

    def __init__(self, mapfilename, project=None, silent=False):

        self.mapfilename = mapfilename
        self.project = project
        self.map_data_arr = []
        self.map_json = {}
        self.silent = silent
        self.publog = log.return_logger('Mapfile Conversion', silent=silent)

    def parse_map(self, mountpoints=None):
        """  """
        ret = []
        for line in self.map_data:

            parts = line.rstrip().split(' | ')
            if mountpoints and self.project:
                mapstr = parts[1]
                root = mapstr.split(self.project)[0][:-1]
                if root in mountpoints:
                    parts[1] = mapstr.replace(root, mountpoints[root])

            ret.append(parts)

        self.map_data_arr = ret
        return ret

    def set_map_arr(self, maparr):
        self.map_data_arr = maparr

    def parse_map_arr(self):
        ''' Input: Takes a 2-D array representation of the parsed map.
        Returns: file records.  assumes that the files all belong to the same dataset
        '''
        if len(self.map_data_arr) == 0:
            self.publog.warning("Empty map data")

        ret = []
        for lst in self.map_data_arr:
            rec = {}
            rec['file'] = lst[1]
            rec['size'] = int(lst[2])
            for x in lst[3:]:
                parts = x.split('=')
                if parts[0] == 'mod_time':
                    rec["timestamp"] = datetime.utcfromtimestamp(float(parts[1])).isoformat()[0:19] + "Z"
                    if rec["timestamp"].find('.') != -1:
                        raise RuntimeError()
                else:
                    rec[parts[0]] = parts[1]
            ret.append(rec)
        return ret

    def load_map_json(self):
        try:
            self.map_json = json.load(open(self.mapfilename))
        except:
            self.publog.error("Could not open json data {}".format(self.mapfilename))

    def mapfilerun(self, mountpoints=None):

        with open(self.mapfilename) as self.map_data:
            ret = self.parse_map(mountpoints)

        return ret
