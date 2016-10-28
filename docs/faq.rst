.. _faq:

FAQ and known issues
====================

Publication to THREDDS fails
****************************

Missing permissions to write catalogs
-------------------------------------

If you don't have the permissions to write to the THREDDS directory the publisher fails with:

::

    $ esgpublish --project test --map test.test.map --service fileservice --noscan --thredds
    Traceback (most recent call last):
      ...
      File "/usr/local/uvcdat/2.2.0/lib/python2.7/site-packages/esgcet-3.1.0-py2.7.egg/esgcet/publish/publish.py", line 269, in publishDatasetList
        threddsOutput = open(threddsOutputPath, "w")
    IOError: [Errno 13] Permission denied: u'/esg/content/thredds/esgcet/1/test.test.v1.xml'

**Solution:**

    Make sure the (unix-) user you use for publication has write access to the THREDDS catalogs, ``/esg/content/thredds/esgcet/``.
    There are a number of ways to manage the permissions. You could, for instance change the group and group-permissions to a group the (unix-) user is member of.

    ::

        $ chgrp -R <group> /esg/content/thredds/esgcet/
        $ chmod -R g+w /esg/content/thredds/esgcet/


Publication to Solr Index fails
*******************************

User is not authorized to publish
---------------------------------

::

    $ esgpublish --project test --map test.test.map --service fileservice --noscan --publish
    INFO       2016-10-28 10:50:46,970 Publishing: test.test
    Traceback (most recent call last):
    ...
    esgcet.publish.hessianlib.RemoteCallException: Java ServiceException: User: https://esgf-data.dkrz.de/esgf-idp/openid/kbtest is not authorized to publish/unpublish resource: http://esgf-dev.dkrz.de/thredds/catalog/esgcet/1/test.test.v1.xml
    ...

**Solution:**

#. Check the permissions
    If you publish to your own index node please check the permissions of the policies files on your **index node**, see section :ref:`policies`
    and also make sure you have the correct permissions for both policies files:

        ::

            -rw-r----- 1 tomcat tomcat 5840 Aug  8 10:32 /esg/config/esgf_policies_local.xml
            -rw-r----- 1 tomcat tomcat 1381 Mar 21  2016 /esg/config/esgf_policies_common.xml

    If you publish to another index node please coordinate with that site's node administrator.
#. Check your server certificate
    Make sure you have a valid server certificate for tomcat.

    ::

        $ openssl s_client -connect <fqdn>:443 2>&1 | openssl x509 -text -noout

    The CN should exactly match the ESGF hostname. In case you use a commercial certificate make sure your root certificate is in the ESGF truststore.
    More information on the certificate generation and installation can be found on our `github installer wiki <https://github.com/ESGF/esgf-installer/wiki/ESGF-CSR-and-Certificate-Installation>`_.
