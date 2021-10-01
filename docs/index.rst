The esgcet package for ESGF Publication
=======================================

Esgcet is a package of publisher commands for publishing to the `ESGF
<https://esgf-node.llnl.gov/projects/esgf-llnl/>`_ search database.


TL;DR
-----

if you have conda you can install the publisher wih the following into a fresh environment:
::
     conda create -n esgf-pub -c conda-forge -c esgf-forge esgcet
     conda activate esgf-pub
     esgpublish # will print the usage information.

You may also look at the inital ``~/.esg/esg.ini`` and fill in the missing information based on the provided examples.

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




