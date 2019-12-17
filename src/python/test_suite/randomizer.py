import sys, os
from random import sample

def get_rand_lines(infile, count):

    return sample([line for line in infile], count)



arr = get_rand_lines(open(sys.argv[1]), 10000)


for i in range(100):


    outf=open("map_batch_{}.lst".format(i+1))

    for j in range(100):

        outf.write(arr[i*100+j])
    outf.close()


