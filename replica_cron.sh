#!/bin/bash

cd /export/ames4/git/esg-publisher

running=`ps -fe | grep pub-2-0 | wc -l`

source ~/conda/etc/profile.d/conda.sh
conda activate esgf-pub-v5
if [ $running -gt 1 ]
then
  exit 0
else
  echo No publisher process detected, starting!
  thedate=`date +%y%m%d_%H%M` ; time nohup python3 pub-2-0.py > /esg/log/publisher/main/replica-pub.$thedate.log
fi
