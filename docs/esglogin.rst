.. _esglogin:

esglogin
========

Publishing to the ESGF STAC catalog requires login credentials from an OAuth provider.  We have two Auth domains for ESGF:  Globus (West publishing) and EGI check-in (EAST).  Please select one of the configurations below
Paste one of the following config into your ``.yaml`` configuraion depending on which ESGF region you intend to publish:
See 

West / Globus Auth config (production)
------------------------------- 

.. code-block:: yaml

stac_config:
  stac_client:
    client_id: 40ef1be1-5d35-4a69-a571-8ca8bec8f211
    redirect_uri: https://auth.globus.org/v2/web/auth-code
  token_storage_file: ~/.esgf-publisher.json
  stac_transaction_api:
    client_id: 66ae998e-9e67-4eea-bf9d-7d0e1eb0946f
    access_control_policy: https://esgf2.s3.amazonaws.com/access_control_policy.json
    scope_string: https://auth.globus.org/scopes/66ae998e-9e67-4eea-bf9d-7d0e1eb0946f/transaction
    base_url: https://transaction.west.esgf.io
  stac_api: https://discovery.west.esgf.io



East / EGI check-in config (production)
---------------------------------------

.. code-block:: yaml

stac_config:
  token_storage_file: ~/.esgf-publisher.json
  stac_transaction_api:
    client_id: 3da9c21e-2bb9-4576-9054-af420514cb7b
    device_endpoint: https://aai.egi.eu/auth/realms/egi/protocol/openid-connect/auth/device
    token_endpoint: https://aai.egi.eu/auth/realms/egi/protocol/openid-connect/token
    base_url: https://transaction.east.esgf.io
  stac_api: https://discovery.east.esgf.io



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

