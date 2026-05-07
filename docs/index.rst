The esgcet package for ESGF Publication - PRE-RELEASE |version|
================================================================


Esgcet is a package of publisher commands for publishing to the `ESGF
<https://esgf-node.ornl.gov/search>`_ search database.


TL;DR
-----

If you have conda or mamba on a Linux system you can install the publisher wih the following into a fresh environment, and update to the latest version (|version|):::

     conda create -n esgf-pub  pip  # most commom
     conda activate esgf-pub
     pip install esgcet  
     esgpublish --version #  Ensure you have upgraded to the version above
     esgpublish # will print the usage information.


.. toctree::
   :maxdepth: 2

   intro
   whatsnew
   install
   autocurator
   cmor
   esglogin
   esgmigrate
   esgpublish
   esgadd
   esgmapconv
   esgmkpubrec
   esgpidcitepub
   esgupdate
   esgindexpub
   esgunpublish
   notebooks
   troubleshooting
   contributing





