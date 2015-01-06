map_file=$1
list_file=$2

list_trimmed=$list_file.tmp1

l_count=`cat $list_file | wc -l`

path_prefix=`head -n 1 $map_file | awk '{print $3}' | awk -v FS='/' '{print "/" $1 "/" $2 "/" $3 "/"}'`

sort $map_file > $map_file.tmp1

head -n $(( $l_count - 2 )) $list_file | tail -n $(( $lcount - 4 )) | awk -v path=$path_prefix '{print path $1 " " $3 }' | sort > $list_trimmed

join -1 1 -2 3 $list_trimmed $map_file.tmp1 | awk '{print $3 " | " $1 " | " $5 " | " $7 " | checksum=" $2 " | checksum_type=MD5" }' | sort > $map_file

