#!/usr/bin/env bash

# recommended shebang....

#CONDA_HOME=$HOME/conda
CONDA_HOME=/usr/local/conda


check_error() {
if [ $? != 0 ] ; then
    
    echo Error has occurred.  Exiting install.  Please report this error to the ESGF development team.
    exit -1
fi
}

if [ -d  $CONDA_HOME ] ; then

    source $CONDA_HOME/bin/activate
else
    # try if in path already
    source activate
fi
check_error
conda create -y -n pub-py3 -c conda-forge cmor cdms2 pip git python=3.7
check_error
conda activate pub-py3
check_error
pip install 'git+https://github.com/IS-ENES-Data/esgf-pid@python_3.7' 'git+https://github.com/sashakames/esdoc-cdf2cim.git'
check_error
pip install  'git+https://github.com/ESGF/esg-publisher@python3#subdirectory=src/python/esgcet'
check_error
 
echo all done!



