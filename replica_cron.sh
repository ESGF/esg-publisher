#!/bin/bash

cd /export/witham3/pub-internal
running=`ps -fe | grep pub-2-0 | wc -l`
export PATH=~/anaconda2/bin:$PATH
. ~/.bashrc
conda activate esgf-pub-v5
if [ $running -gt 1 ]
then
  exit 0
else
  python3 pub-2-0.py
fi
