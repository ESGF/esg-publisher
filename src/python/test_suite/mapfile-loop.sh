prefix=$HOME/pub-test/maps

for fn in `cat $1` ; do

    
    esgpublish --project cmip6 --test --map $prefix/$fn

    if [ $? != 0 ] ; 
	then

	continue
    fi
done


for fn in `cat $1` ; do

    esgpublish --project cmip6 --test --map $prefix/$fn --noscan --thredds --no-thredds-reinit --service fileservice
    if [ $? != 0 ] ; 
	then

	continue
    fi
done

esgpublish --project cmip6 --test --thredds-reinit
