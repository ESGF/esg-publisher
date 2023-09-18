CMOR
====

Before running the publisher for CMIP6, you will need to obtain a directory of CMOR tables, used by PrePARE to check the metadata of your files.
You can get this directory either using ``esgprep`` or by cloning the git repository.  CMOR/PrePARE is available for Linux and MacOS Intel.  Mac Apple M1 systems are not currently supported.

NOTE: ``esgprep`` uses python 2.6 or greater, but less than python 3.0. Configure your virtual environment as needed.

esgprep
-------

You can install ``esgprep`` (esgf-prepare) using pip::

    pip install esgprep

You can also clone their git repository and run setup.py::

    git clone git://github.com/ESGF/esgf-prepare.git
    cd esgf-prepare
    python setup.py install

Following install, simply run::

    esgfetchtables

You can specify project using ``--project`` and the output directory using ``--table-dir`` like so::

    esgfetchtables --project CMIP6 --table-dir <path>

Once you have fetched the tables, you can update the ``cmor_path`` variable in your config file, or specify it at run time in the command line.
See https://esgf.github.io/esgf-prepare/ for more information.

Clone Git Repository
--------------------

Clone the repository::

    git clone https://github.com/PCMDI/cmip6-cmor-tables.git

Your tables will be in the folder ``cmip6-cmor-tables/Tables`` (unless you specify a different target directory name for the clone).
You can now update the ``cmor_path`` variable in your config file, or specify it at run time in the command line.