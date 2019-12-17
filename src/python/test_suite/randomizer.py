import sys, os
from random import sample

NUM_BATCHES = 100
NUM_PER_BATCH = 100

def get_rand_lines(infile, count):

    return sample([line for line in infile], count)



arr = get_rand_lines(open(sys.argv[1]), NUM_BATCHES * NUM_PER_BATCH)


for i in range(NUM_BATCHES):


    outf=open("map_batch_{}.lst".format(i+1))

    for j in range(NUM_PER_BATCH):

        outf.write(arr[i*NUM_PER_BATCH+j])
    outf.close()


