The esgcet package for ESGF Publication - Version 5.2.0
=========================================================

Esgcet is a package of publisher commands for publishing to the `ESGF
<https://esgf-node.llnl.gov/projects/esgf-llnl/>`_ search database.


TL;DR
-----

if you have conda you can install the publisher wih the following into a fresh environment, and update to the latest version:
::
     conda create -n esgf-pub -c conda-forge -c esgf-forge esgcet
     conda activate esgf-pub
     pip install esgcet  
     esgpublish --version #  Ensure you have upgraded to v5.2.0
     esgpublish # will print the usage information.

You may also look at the inital ``~/.esg/esg.yaml`` and update to fit your site configuration.

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
   troubleshooting
   contributing




