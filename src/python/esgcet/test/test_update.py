from esgcet.update_globus import ESGUpdateGlobus
import sys

UUID = "5cc79324-1b74-4a77-abc3-838aba2fc734"

def test(args):
    rec = [{},{"master_id" : args[0], 
               "data_node" : args[1]}]
    gup = ESGUpdateGlobus(UUID, sys.argv[1])

    gup.run(rec)
    
test(sys.argv[0:2])