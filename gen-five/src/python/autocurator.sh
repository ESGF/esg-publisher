
autocur_cmd=$1
fullmap=$2
scanfn=$3
path=`head -n1 $fullmap | awk '{print $3}'`
datasetdir=`dirname ${path}`/'*.nc'
$autocur_cmd --out_pretty --out_json $scanfn --files "$datasetdir"
