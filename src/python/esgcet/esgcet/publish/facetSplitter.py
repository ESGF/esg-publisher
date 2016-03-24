import csv
from StringIO import StringIO


class FacetSplitter:

    """
    A class that splits multi-valued facets into a list based on whatever 
    delimiter is read in from the configuration file.  Example usage:

        splitter = FacetSplitter(delimiter)
        bits = splitter(facet_value)

    The allowed delimiter values are as follows:

          None     - do not split strings, just wrap them in a list of length 1

          'space'  - split using any amount of whitespace

          'csv'    - split using the csv module (similar to splitting on ',' 
                     but also allows commas inside quoted values)

          any string whose value starts and 
          ends with quotes (single or double)

                   - split using the delimiter with the outer quotes removed
 
                     This may help with delimiters that start or end with
                     whitespace.  The config parser won't strip the quotes,
                     but this class will.

          anything else - use as literal delimiter

    If the splitter operates on '' (or on whitespace with delimiter='space')
    it normally returns [''].  But if allow_empty_list=True was passed in when
    instantiating then it will return [] (except that when delimiter==None the
    returned list is length 1 regardless).

    """

    def __init__(self, delim, allow_empty_list=False):

        if allow_empty_list:
            self._if_empty = []
        else:
            self._if_empty = ['']

        self._split = self._normal_split

        if delim == None:
            self._split = None

        elif delim == 'space':
            self._sep = None

        elif delim == 'csv':
            self._split = self._csv_split

        elif (len(delim) > 1
              and delim[0] == delim[-1] 
              and delim[0] in ('"', "'")):
            self._sep = delim[1 : -1]

        else:
            self._sep = delim

    def _normal_split(self, value):

        return value.split(self._sep)

    def _csv_split(self, value):

        split_lines = [x for x in csv.reader(StringIO(value + "\n"))]
        return split_lines[0]
        
    def __call__(self, value):

        if self._split == None:
            return [value]

        bits = self._split(value)

        if bits in ([], ['']):
            return self._if_empty
        else:
            return bits


if __name__ == '__main__':
    
    for delim, value1 in [
            ('space', 'firstThing secondThing   thirdThing'),
            (',',   'first thing,second thing,third thing'),
            ('csv', 'first thing,"second, thing",third thing'),
            ("' '", 'firstThing secondThing  fourthThing'),
            ('#', 'first thing#second thing#third thing'),
            (None, 'whatever...')
        ]:

        print "using delimiter: %s" % repr(delim)
        print

        splitter = FacetSplitter(delim)
        #splitter = FacetSplitter(delim, allow_empty_list = True)

        for value in (value1, 'onlyThing', ''):
            print "   splitting '%s'" % value
            print "   gives %s" % splitter(value)
            print
