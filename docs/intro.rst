Publisher Introduction
======================

The **esg-publisher** or ``esgcet`` Python package contains a collection of command-line utilities to scan, manipulate and push dataset metadata to an *ESGF index node*.  The basic publication process includes several basic steps and sometimes `optional` steps. Publisher functionality is available via several submodles/classes in the package. 


The publisher software has undergone a significant change starting with v5.* of the software.  Prior versions involved storage of dataset metadata in the legacy ESGF data node PostgreSQL database and generation of `THREDDS` catalogs.   The actual publication to the ESGF index occured via catalog harvesting.  Instead, the more recent publisher simplifies the process with the following phases:

#. Local scan of datasets (featuring the ``autocurator`` package by default)
#. Record generation using scan, mapfile and auxiliary (json) information/files as input
#. Update check of existing dataset, previous version manipulation.
#. Push/publish of record(s) to ESGF index

And several `optional` project-specific phases:

* Automatic metadata checking with PrePARE (CMIP6-only as of today)
* PID registration and citiation URL generation (CMIP6 and input4MIPs)

For those familiar with the previous publisher, please be aware of the following distinctions between earlier versions and v5.* 

* A Python3 conda environment is required (most prior versions have run Python2)
* the configuration (.ini) file format is new and have been vastly simplified.  Note that the old format for project-specific .ini files are still used by the esgf-prepare tools (eg. esgmapfile).  The v5. publisher has the ability to migrate the needed settings from the previous ini files.
* Prior invocation of esgpublish required use of ``--thredds`` and ``--publish`` stages.  Those arguments are eliminated.  In the general case, you can run esgpublish in a single command.  Advanced users may chose to run the individual publishing steps separately to create workflows, for instance, in the use of an external workflow manager. 


Prerequisites
-------------

* ``conda`` eg. `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_  installation.
* Mountpoint to located data on the same host as publisher software installation, so the publisher scan utility (eg. ``autocurator``) has access.
* Basic dataset information provided via the esg mapfile format.   The most popular approach is using the `esgf-prepare/esgmapfile <https://esgf.github.io/esgf-prepare/>`_ utility.


