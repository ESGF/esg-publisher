The esgcet package for ESGF Publication - Version 5.3.4
=======================================================

Esgcet is a package of publisher commands for publishing to the `ESGF
<https://aims2.llnl.gov/search>`_ search database.


TL;DR
-----

If you have conda or mamba on a Linux system you can install the publisher wih the following into a fresh environment, and update to the latest version:::

     conda create -n esgf-pub  pip  # most commom
     conda activate esgf-pub
     pip install esgcet  
     esgpublish --version #  Ensure you have upgraded to v5.3.4
     esgpublish # will print the usage information.


.. toctree::
   :maxdepth: 2

   intro
   whatsnew
   install
   autocurator
   cmor
   esgmigrate
   esgpublish
   esgmapconv
   esgmkpubrec
   esgpidcitepub
   esgupdate
   esgindexpub
   esgunpublish
   notebooks
   troubleshooting
   contributing





