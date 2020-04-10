export LD_LIBRARY_PATH=$CONDA_PREFIX/lib

NUM_TODO=20

maps_in=$1
dt=`date +%y%m%d_%H%M`
target_file=/tmp/maps_todo_${dt}
py_src_path=/export/ames4/git/esg-publisher/gen-five/src/python
autocur_cmd="/export/ames4/git/autocurator/bin/autocurator --out_pretty true"
mapconv_cmd=$py_src_path/mapfile.py  # convert mapfile to json
mkds_cmd=$py_src_path/mk_dataset.py  # make dataset from sources

cert_path=$HOME/cert.pem

ls $maps_in | head -n $num_todo | sed s:^:${maps_in}/:g > $target_file

if [ $? != 0 ] ; then
    echo No Mapfiles exiting 1
    exit
fi

for fn in `cat $target_file`; do

path=`head -n1 $dir/$fn | awk '{print $3}'`
datasetdir=`dirname ${path}`/'*.nc'
basefn=`basename $fn`

strfn="${basefn%.*}"
scanfn=$strfn.scan.json
convmapfn=$strfn.map.json

$autocur_cmd --out_file $scanfn --files "$val"
#python $mapconv_cmd 


done
