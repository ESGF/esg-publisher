.. _esglogin:

esglogin
========

Publishing to the ESGF STAC catalog requires login credentials from an OAuth provider.  We have two Auth domains for ESGF:  Globus (West publishing) and EGI check-in (EAST).  Please select one of the configurations below
Paste one of the following config into your ``.yaml`` configuraion depending on which ESGF region you intend to publish:


Globus Auth config
------------------

.. code-block:: yaml

    stac_config:
        stac_client:
            client_id:  ec5f07c0-7ed8-4f2b-94f2-ddb6f8fc91a3
            redirect_uri:  https://auth.globus.org/v2/web/auth-code
        token_storage_file: ~/.esgf2-publisher.json
        stac_transaction_api:
            client_id: 6fa3b827-5484-42b9-84db-f00c7a183a6a
            access_control_policy: https://esgf2.s3.amazonaws.com/access_control_policy.json
        #    scope_string: https://auth.globus.org/scopes/ec5f07c0-7ed8-4f2b-94f2-ddb6f8fc91a3/ingest
            scope_string: https://auth.globus.org/scopes/6fa3b827-5484-42b9-84db-f00c7a183a6a/ingest    
            base_url: https://client-integration-transaction.api.stac.esgf-west.org
        stac_api: https://api.stac.esgf-west.org




EGI check-in config
-------------------

.. code-block:: yaml

    stac_config:
        token_storage_file: ~/.esgf2-publisher-egi.json
        stac_transaction_api:
            client_id: 3da9c21e-2bb9-4576-9054-af420514cb7b
            device_endpoint: https://aai.egi.eu/auth/realms/egi/protocol/openid-connect/auth/device
            token_endpoint: https://aai.egi.eu/auth/realms/egi/protocol/openid-connect/token
            scope: 'offline_access entitlements'
            base_url: https://api.stac.esgf.ceda.ac.uk
        stac_api: https://api.stac.esgf.ceda.ac.uk

Command Usage
-------------

``esglogin`` is used with the following::

        usage: esglogin [-h] [--config CFG]

    One-time login to fetch necessary OAuth2 token, required to publish ESGF STAC
    Transaction API. Ensure that you have configured your .yaml file with the
    correct API settings prior to use.

        options:
        -h, --help              show this help message and exit
        --config CFG, -cfg CFG  Path to .yaml config file.

