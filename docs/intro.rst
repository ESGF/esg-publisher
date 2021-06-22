Publisher Introduction
======================

The **esg-publisher** or ``esgcet`` package is Python module, a collection of command-line utilities to scan, manipulate and push dataset metadata to an *ESGF index node*.  The basic publication process includes several basic steps and sometimes `optional` steps. Publisher functional


The publisher software has undergone a significant change starting with v5.* of the software.  Prior versions involved storage of dataset metadata and generation of `THREDDS` catalogs.   The actual publication to the ESGF index occured via catalog harvesting.  Instead, the more recent publisher simplifies the process with the following phases:

#. Local scan of datasets (featuring the ``autocurator`` package by default)
#. Record generation using scan, mapfile and auxiliary (json) information/files as input
#. Update check of existing dataset, previous version manipulation.
#. Push/publish of record(s) to ESGF index

And several `optional` project-specific phases:

* Automatic metadata checking with PrePARE (CMIP6-only as of today)
* PID registration and citiation URL generation (CMIP6 and input4MIPs)
 
Prerequisites
-------------

* ``conda`` eg. `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_  installation.
* Mountpoint to located
* Basic dataset information provided via the esg mapfile format.   The most popular approach is using the 
`esgf-prepare/esgmapfile <https://esgf.github.io/esgf-prepare/>`_ 
utility.
