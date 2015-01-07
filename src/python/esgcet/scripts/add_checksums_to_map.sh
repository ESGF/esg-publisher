if [ $# -lt 2 ] ; then
    echo Usage:  
    echo     add_checksums_to_map.sh '<map-file> <list-file>'
    echo
    echo Where the '<list-file>' contains the checksums
    exit
fi


map_file=$1
list_file=$2

list_trimmed=`basename $list_file`.tmp1

l_count=`cat $list_file | wc -l`

echo "List file length (including head/foot):" $l_count

path_prefix=`head -n 1 $map_file | awk '{print $3}' | awk -v FS='/' '{print "/" $2 "/" $3 "/"}'`

sort $map_file > $map_file.tmp1

head -n $(( $l_count - 2 )) $list_file | tail -n $(( $l_count - 4 )) | awk -v path=$path_prefix '{print path $1 " " $3 }' | sort > $list_trimmed

join -1 1 -2 3 $list_trimmed $map_file.tmp1 | awk '{print $3 " | " $1 " | " $6 " | " $8 " | checksum=" $2 " | checksum_type=MD5" }' | sort > $map_file

