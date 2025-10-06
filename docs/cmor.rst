CMOR Table input
================

Before running the publisher for CMIP6, you will need to obtain a directory of CMOR Tables, used by ``esgpublish`` to check the metadata of your files.
The CMOR table files are used by the publisher for DRS property validation.
The tables must be fetched from Github prior to publishing.
As of v5.3.2 PrePARE is no longer run to check CMIP6 data (deprecated module).

Clone Git Repository
--------------------

Clone the repository::

    git clone https://github.com/PCMDI/cmip6-cmor-tables.git

Your tables will be in the folder ``cmip6-cmor-tables/Tables`` (unless you specify a different target directory name for the clone).
You can now update the ``cmor_path`` variable in your config file, or specify it at run time in the command line.


