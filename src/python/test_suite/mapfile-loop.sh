maplists=$1
prefix=$HOME/pub-test/maps

for lfn in `ls $maplists` ; do

    stop=`cat /tmp/pub_status`
    if [ $stop == "true" ] ; then
        exit    
    fi

    for mfn in `cat $maplists/$lfn` ; do    
        esgpublish --project cmip6 --test --map $prefix/$mfn

        if [ $? != 0 ] ; 
    	then

    	continue
        fi
    done


    for mfn in `cat $maplists/$lfn` ; do

        esgpublish --project cmip6 --test --map $prefix/$mfn --noscan --thredds --no-thredds-reinit --service fileservice
        if [ $? != 0 ] ; 
    	then

    	continue
        fi
    done

    esgpublish --project cmip6 --test --thredds-reinit
done
