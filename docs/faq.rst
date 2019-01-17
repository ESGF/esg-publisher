.. _faq:

FAQ and known issues
====================

PID Configuration
*****************

Cannot connect to PID server
----------------------------

Please ensure that the firewall is open for all PID hosts in your ``[config:<project>]`` section, port 5671.

If you can't connect to the server the publisher will produce the following errors:

::

    $ esgpublish --test --project test --map test.test.map --service fileservice --noscan --thredds
        ...
        INFO       2017-11-14 18:50:23,729 Opening connection to RabbitMQ...
        INFO       2017-11-14 18:50:23,792 Connecting to 198.128.245.160:5671 with SSL
        ERROR      2017-11-14 18:50:24,042 Connection to 198.128.245.160:5671 failed: timeout
        WARNING    2017-11-14 18:50:24,042 Could not connect, 0 attempts left
        ERROR      2017-11-14 18:50:24,042 Could not connect to pcmdi10.llnl.gov/esgf-pid:5671: "Connection to 198.128.245.160:5671 failed: timeout" (connection failure after 0.313869 seconds)
        ...


Setting up PID credentials
--------------------------

In case the publisher fails with one of the following errors please make sure your ``[config:<project>]`` section is set up correctly and does contain the ``pid_credentials``.
For more information see section :ref:`The project config section <config_project_section>`

::

    Section 'config:cmip6' not found in esg.ini

::

    Option 'pid_credentials' missing in section [config:<project>] of esg.ini. Please contact your tier1 data node admin to get the proper values.


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


myproxy-logon fails
*******************

tlsv1 alert unknown ca
----------------------

If you run myproxy-logon as (unix-) user root it might fail with the following error:

::

    $ myproxy-logon -s esgf-data.dkrz.de -l test_user -b -t 72 -o $HOME/.globus/certificate-file

    Error authenticating: GSS Major Status: Authentication Failed
    GSS Minor Status Error Chain:
    globus_gss_assist: Error during context initialization
    globus_gsi_gssapi: Unable to verify remote side's credentials
    globus_gsi_gssapi: SSLv3 handshake problems: Couldn't do ssl handshake
    OpenSSL Error: s3_pkt.c:1259: in library: SSL routines, function SSL3_READ_BYTES: tlsv1 alert unknown ca SSL alert number 48

**Solution:**

    It is not recommended to publish as (unix-) user root, please use another user for publication. The publication as root might also have a number of other side-effects.


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


Miscellaneous
*************

Configuration file option missing
---------------------------------
::

    ...
    esgcet.exceptions.ESGPublishError: Configuration file option missing: hessian_service_certs_location in section: DEFAULT, file=/esg/config/esgcet/esg.ini

**Solution**

- Add the following to /esg/config/esgcet/esg.ini

    :: 

        hessian_service_certs_location = %(home)s/.globus/certificates

    The certificates are fetched during the myproxy-login -b (bootstrap)

THREDDS does not unpublish
--------------------------

- Staring in v3.4.4  esgunpublish is reconfigured to use the REST API by default.  You will need to unpublish with --skip-index and use a list of datasets with versions with the ``.vYYYYMMDD`` or ``.vNN`` format instead of ``#YYYYMMDD``, etc.

Error Running Publisher in nohup (or other) scripted environment
----------------------------------------------------------------

- You may see an error like this following a stack trace with UVCDAT_ANONYMOUS_LOG:


::

    ...
    IOError: [Errno 9] Bad file descriptor

**Solution**

- You msut diasable the UVCDAT anonymous logging as the user prompt will repeat periodically.  Add to your script before calling esgpublish.

::

        $ export UVCDAT_ANONYMOUS_LOG=no

