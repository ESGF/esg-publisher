
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib

NUM_TODO=20
proj=CMIP6

maps_in=$1

dt=`date +%y%m%d_%H%M`

target_file=/tmp/maps_todo_${dt}
py_src_path=/export/ames4/git/esg-publisher/gen-five/src/python
autocur_cmd="/export/ames4/git/autocurator/bin/autocurator --out_pretty true"
mapconv_cmd=$py_src_path/mapfile.py  # convert mapfile to json
mkds_cmd=$py_src_path/mk_dataset.py  # make dataset from sources
idx_pub_cmd=$py_src_path/pub_test.py
update_cmd=$py_src_path/update.py
chk_cmd=$py_src_path/activity_check.py



cert_path=$HOME/cert.pem

check_error() {
if [ $? != 0 ] ; then
    
    echo Error has occurred.  Exiting install.  Please report this error to the ESGF development team.
    exit -1
fi
}

#ls $maps_in | head -n $num_todo | sed s:^:${maps_in}/:g > $target_file


if [ $? != 0 ] ; then
    echo No Mapfiles exiting 1
    exit
fi

target_file=$1
#dir=/export/ames4/pub-test/maps
dir=/p/user_pub/publish-queue/CMIP6-maps-todo


for fn in `cat $target_file`; do

    fullmap=$dir/$fn

    path=`head -n1 $fullmap | awk '{print $3}'`
    datasetdir=`dirname ${path}`/'*.nc'
    basefn=`basename $fn`


    strfn="${basefn%.*}"
    scanfn=$strfn.scan.json
    convmapfn=$strfn.map.json

    $autocur_cmd --out_json $scanfn --files "$datasetdir"
    python $mapconv_cmd $fullmap $proj > $convmapfn
    python $mkds_cmd $convmapfn $scanfn > $strfn.out.json
    python $update_cmd $strfn.out.json
    check_error
    python $chk_cmd $strfn.out.json
    check_error
    python $idx_pub_cmd $strfn.out.json

done
