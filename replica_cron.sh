#!/bin/bash

cd /export/witham3/pub-internal
running=`ps -fe | grep pub-2-0 | wc -l`
if [ $running -gt 0 ]
then
  exit 0
else
  python3 pub-2-0.py
fi
