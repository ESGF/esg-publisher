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
conda create -n esgf-pub-v5 -c conda-forge gcc pip requests libnetcdf

# Follow the autocurator instructions.  Use the esgf-pub-v5 environment for building that binary
# See https://github.com/sashakames/autocurator 
# edit gen-five/src/python/settings.py  and gen-five/src/workflow/esgpublish.sh for system-specific settings

# run the shell-script with a mapfile

bash gen-five/src/workflow/esgpublish.sh <mapfile>

