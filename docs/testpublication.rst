.. _testpublication:

Quick guide to test publication
===============================

You can either use the prepared test script to run a publication test or you can execute some manual steps.

Use the script: esgtest_publish
*******************************

Preliminary
-----------

Set up default environment for scripts:

::

ESGF v2.5 or later

    $ source /usr/local/conda/bin/activate esgf-pub

ESGF v2.4.x or earlier

    $ source /etc/esg.env


Run the test script
-------------------

::

    $ esgtest_publish


**The above command will go through all steps of the publication:**

#. Check whether the current (unix-)user has write permissions to the appropriate directories
#. Generate a globus certificate, if not already present
#. Download a test file, if not already present
#. Generate a mapfile
#. Publish to Postgres, THREDDS and Solr in separate steps and verify publication
#. Unpublish and verify unpublication for all three components
#. Clean up: Delete the mapfile but keep globus certificate and test file

By default the script will publish to all three components: Postgres, THREDDS and Solr. But you can also skip some tests:

    ::

        $ esgtest_publish --skip-index      # Skip publication to the Solr Index
        $ esgtest_publish --skip-thredds    # Skip publication to THREDDS and Solr Index


**Possible options to specify the credentials for the globus cert:**

- Specify the credentials as options:

    ::

        $ esgtest_publish --myproxy-host <openid_server> --myproxy-user <esgf_user> --myproxy-pass <password>

- Add the information to your ``esg.ini`` file, section ``myproxy``:

    ::

        [myproxy]
        hostname = <openid_server>
        username = <esgf_user>
        password = <password>

- Simply fill out the user prompts during the script runtime.

.. note::
    If you are running an "all" ESGF node installation and the credentials are not specified otherwise the script will use
    the ``rootAdmin`` account and get the appropriate password automatically.


Manual steps
************

Preliminary
-----------

Set up default environment for scripts:

::

ESGF v2.5 or later

    $ source /usr/local/conda/bin/activate esgf-pub

ESGF v2.4.x or earlier

    $ source /etc/esg.env


Generate a valid globus certificate. For publication of test data you could use ``esgf_user`` rootAdmin, this account has preset permissions to publish test data.

::

    $ myproxy-logon -s <openid_server> -l <esgf_user> -b -t 72 -o $HOME/.globus/certificate-file


Configuration
-------------

The configuration file for project test should already be present in the default location: ``/esg/config/esgcet/esg.test.ini``. In case it is missing fetch it with ``esgprep fetch-ini``:

::

    $ esgprep fetch-ini --project test


Make sure you have values for project test in the ``project_options`` and ``thredds_dataset_roots`` in ``/esg/config/esgcet/esg.ini``:

::

    project_options =
        cmip5 | CMIP5        | 1
        test  | Test Project | 2
        ...   | ...          | ...

    thredds_dataset_roots =
        cmip5 | /esg/data/cmip5
        test  |  /esg/data/test
        ...   | ...


Download test file
------------------

::

    $ cd /esg/data/test
    $ rm sftlf.nc
    $ wget -O sftlf.nc http://distrib-coffee.ipsl.jussieu.fr/pub/esgf/dist/externals/sftlf.nc


Mapfile generation
------------------

::

    $ esgprep mapfile --project test /esg/data/test

The above will generate a mapfile ``test.test.map`` in your working directory.

::

    $ cat test.test.map
    test.test | /esg/data/test/sftlf.nc | 5 | mod_time=1469535544.68 | checksum=f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2 | checksum_type=SHA256


Publication
-----------

Publish to local postgres database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

   $ esgpublish --project test --map test.test.map --service fileservice


Publish to local Thredds server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

   $ esgpublish --project test --map test.test.map --service fileservice --noscan --thredds

.. warning::
    Make sure the (unix-) user you use for publication has write access to the THREDDS catalogs in ``/esg/content/thredds/esgcet/``.


Publish to index node
^^^^^^^^^^^^^^^^^^^^^

::

   $ esgpublish --project test --map test.test.map --service fileservice --noscan --publish

.. note::
    If you publish to another index please coordinate with that site's node administrator.

.. note::
    If the above step fails check the publishing permissions, see section :ref:`policies`.


Unpublication
-------------

If you are on a production node please make sure to unpublish the test file after successful publication. Test data should not be visible to users.

    ::

        $ esgunpublish --map test.test.map
