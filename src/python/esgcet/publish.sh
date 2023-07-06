successdir=/p/user_pub/publish-queue/CMIP6-maps-done
faildir=/p/user_pup/publish-queue/CMIP6-maps-err

tmpdir=/export/witham3/tmplogs

basemap=`basename $1`
map=$1

python3 gen-five/src/python/pub-internal.py --map $map > $tmpdir/$basemap.log 2>&1

success=`grep success $tmpdir/$basemap.log | wc -l | tr -d '\n'`

if (( $success < 2 ))
then
  mv $map $faildir/$basemap
  mv $tmpdir/$basemap.log $faildir/$basemap.log
else
  mv $map $successdir/$basemap
fi
