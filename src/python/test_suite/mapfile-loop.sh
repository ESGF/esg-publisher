prefix=$1

for lfn in `ls $prefix` ; do

    stop=`cat /tmp/pub_status`
    if [ $stop == "true" ] ; then
        exit    
    fi

    for mfn in `cat $lfn` ; do    
        esgpublish --project cmip6 --test --map $prefix/$mfn

        if [ $? != 0 ] ; 
    	then

    	continue
        fi
    done


    for mfn in `cat $1` ; do

        esgpublish --project cmip6 --test --map $prefix/$mfn --noscan --thredds --no-thredds-reinit --service fileservice
        if [ $? != 0 ] ; 
    	then

    	continue
        fi
    done

    esgpublish --project cmip6 --test --thredds-reinit
done