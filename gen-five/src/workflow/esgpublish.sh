export LD_LIBRARY_PATH=$CONDA_PREFIX/lib

proj=CMIP6

dt=`date +%y%m%d_%H%M`

py_src_path=/path/to/esg-publisher/gen-five/src/python
autocur_cmd="/path/to/autocurator/bin/autocurator --out_pretty true"
mapconv_cmd=$py_src_path/mapfile.py  # convert mapfile to json
mkds_cmd=$py_src_path/mk_dataset.py  # make dataset from sources
idx_pub_cmd=$py_src_path/pub_test.py

update_cmd=$py_src_path/update.py

cert_path=./cert.pem



if [ ! -f $1 ] ; then
    echo Error mapfile parameter missing or not found
    exit 1
fi

fullmap=$1

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
python $idx_pub_cmd $strfn.out.json

