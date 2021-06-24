# ESGF Publisher
[![Documentation Status](https://readthedocs.org/projects/esg-publisher/badge/?version=refactor)](https://esg-publisher.readthedocs.io/en/refactor/?badge=refactor)
##### The v5 version of the publisher, scans data and writes metadata to the ESGF index.

## How to test it (with conda)

#### Prerequesites: ESGF publication mapfile generated via esgf-prepare esgmapfile (esgprep package), conda installation

```

# Clone this repository

git clone https://github.com/lisi-w/esg-publisher.git

# Checkout the refactor branch

cd esg-publisher
git checkout refactor

# Ensure you have activate conda 
# create an environment for testing with prereqs
conda create -n esgf-pub -c conda-forge pip requests libnetcdf cmor autocurator
# CMOR needed for CMIP6 publishing
conda activate esgf-pub
pip install esgfpid # needed for publishing
cd pkg
python setup.py install 
# edit $HOME/.esg/esg.ini for system-specific settings

#  For CMIP6 publishing you need the cmor tables.  All files in CMIP6 must pass PrePARE. Options:
#  (1)  git clone https://github.com/PCMDI/cmip6-cmor-tables
#  (2)  If you have esgprep (esgf-prepare) installed, run esgfetchtables
#  edit cmor_path in esg.ini or use --cmor-tables arg to point to the directory containing the tables

# run the executable with a mapfile

esgpublish --map <mapfile>

# for more details on the other commands, see our docs
