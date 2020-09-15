
for basefn in `ls *.map` ; do

injsonfn=`python mapfn2jsonfn.py $basefn`

strfn="${basefn%.*}"
scanfn=$strfn.scan.json
convmapfn=$strfn.map.json
outfn=$strfn.out.json

cmd="bash ../autocurator/autocurator.sh ../autocurator/bin/autocurator $basefn $scanfn"
$cmd
if [ $? != 0 ] ; then

    echo 
    echo [FAIL] $cmd
    echo
    exit
fi

esgmapconv $basefn > $convmapfn

cmd="esgmkpubrec $convmapfn $scanfn $injsonfn"
$cmd > $outfn
if [ $? != 0 ] ; then

    echo 
    echo [FAIL] $cmd
    echo
    exit
fi
cmd="esgpidcitepub $outfn"
$cmd
if [ $? != 0 ] ; then

    echo 
    echo [FAIL] $cmd
    echo
    exit
fi
cmd="esgindexpub $outfn"
$cmd
if [ $? != 0 ] ; then

    echo 
    echo [FAIL] $cmd
    echo
    exit
fi


mv $strfn.* done

done
