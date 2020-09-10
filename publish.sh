successdir=/p/user_pub/publish-queue/CMIP6-maps-done
faildir=/p/user_pub/publish-queue/CMIP6-maps-err

tmpdir=/export/witham3/tmplogs
errorlogs=/export/witham3/error-logs

basemap=`basename $1`
map=$1
fullmap=/p/user_pub/publish-queue/CMIP6-maps-todo/$map

python3 gen-five/src/python/pub-internal.py --map $fullmap > $tmpdir/$basemap.log 2>&1

success=`grep success $tmpdir/$basemap.log | wc -l | tr -d '\n'`
pid=`grep AMQPConnectionError $tmpdir/$basemap.log | wc -l | tr -d '\n'`
server=`grep "server encountered an unexpected condition" $tmpdir/$basemap.log | wc -l | tr -d '\n'`
stale=`grep "Stale file handle"  $tmpdir/$basemap.log | wc -l | tr -d '\n'`
css03=`grep "Unable to open" $tmpdir/$basemap.log | wc -l | tr -d '\n'`
auto=`grep "ERROR: Variable" $tmpdir/$basemap.log | wc -l | tr -d '\n'`

if (( $success < 2 ))
then
  echo error $map
  if (( $pid > 0 ))
  then
    echo pid error
    # keep in current directory -- todo
  elif (( $server > 0 ))
  then
    echo server error
    # keep in current directory -- todo
  elif (( $stale > 0 ))
  then
    echo filesystem error
    exit -1
  elif (( $css03 > 0 ))
  then
    echo /p/css03 error
    # keep in current dir
  elif (( $auto > 0 ))
  then
    echo autocurator error
    mv $fullmap $faildir/
    mv $tmpdir/$basemap.log $errorlogs/autocurator/
  else
    mv $fullmap $faildir/
    mv $tmpdir/$basemap.log $errorlogs/
  fi
else
  mv $fullmap $successdir/
fi
