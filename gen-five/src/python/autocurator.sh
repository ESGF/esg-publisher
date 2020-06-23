
fullmap=$2
scanfn=$3
path=`head -n1 $fullmap | awk '{print $3}'`
datasetdir=`dirname ${path}`/'*.nc'
autocur_cmd=$1
$autocur_cmd --out_json $scanfn --files "$datasetdir"
