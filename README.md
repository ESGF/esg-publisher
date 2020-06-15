# ESGF Publisher

##### The v5 version of the publisher, scans data and writes metadata to the ESGF index.
The PostgreSQL database and THREDDS catalogs are not used

## How to test it (with conda)

#### Prerequesites: ESGF publication mapfile generated via esgf-prepare esgmapfile (esgprep package), conda installation

```

# Clone this repository

git clone https://github.com/sashakames/esg-publisher.git

# Checkout the gen-five branch

cd esg-publisher
git checkout gen-five

# Ensure you have activate conda 
# create an environment for testing with prereqs
conda create -n esgf-pub-v5 -c conda-forge gcc pip requests libnetcdf cmor # needed for CMIP6 publishing

# Follow the autocurator instructions.  Use the esgf-pub-v5 environment for building that binary
# See https://github.com/sashakames/autocurator 
# edit gen-five/src/python/settings.py  and gen-five/src/workflow/esgpublish.sh for system-specific settings

#  For CMIP6 publishing you need the cmor tables.  All files in CMIP6 must pass PrePARE. Options:
#  (1)  git clone https://github.com/PCMDI/cmip6-cmor-tables
#  (2)  If you have esgprep (esgf-prepare) installed, run esgfetchtables
#  update the $cmor_tables variable in esgpublish.sh with path to tables [ Tables from (1) | master from (2) ] above

# run the shell-script with a mapfile

bash gen-five/src/workflow/esgpublish.sh <mapfile>

