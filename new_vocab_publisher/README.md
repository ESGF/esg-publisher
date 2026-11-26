# New Publisher - ESGVOC Integration

IMPORTANT NOTE: The new publisher is in a beta testing stage as it does not yet have proper integration with the main publisher. The old publisher command `esgpublish` cannot be used with this version currently.

The new publisher module is built using some of the existing `esg-publisher` components but is mostly built from scratch for ESGF-NG around the `esgvoc` vocabulary management package. The publisher can therefore publish versions of datasets based on any existing `esgvoc` registry version of any project with a set of CVs. This has primarily been done for the `obs4MIPs` project, newly added to `esgvoc` from November 2026. Integration with esgvoc means:
- No custom logic per-project for extracting attributes: All specifications are pulled from the CVs
- No use of older technologies: This publisher only publishes to STAC.

It is advised to first create STAC records locally with `--save-stac` and `--dry-run` on the publish command to double check everything looks correct. The publisher will also generate warnings and errors on invalid data. It is also important to check that the remote hrefs generated for the assets are correct. Report any problems by creating an issue to this repo.

## Setup - Esgvoc

This package uses `esgvoc` to handle CV management. This is installed with the dependencies, but also needs you to `use` the project and version as required. The example below uses the `latest` version of `obs4mips` - which is also the same label as is used in the config file under `project`.

```
esgvoc use obs4mips@latest
```


## Setup - Permissions

To apply for permissions for your account on EGI to use the publisher, use https://aai.egi.eu/auth/realms/id/account/#/enroll?groupPath=/esgf.vo.egi.eu/project/obs4MIPs, sign into your EGI account and request the obs4MIPs project 'CREATE' and 'UPDATE' permissions.

## Setup - Mapfiles
The publisher still uses map files produced by the `esgprep` package, see the documentation at https://esgf.github.io/esgf-prepare/getting_started.html#step-5-generate-mapfiles on how to generate map files.

## Setup - Config
The new publisher also takes a YAML config file extremely similar to the original, but with some minor changes where it is worth noting the meaning of all elements.

```
data_node: ceda.ac.uk # Will be set as the alternate:site name for all assets and is used with `https://esgf.` to generate the remote download path.
stac_api: https://search-int.east.esgf.io # STAC API (east or west) for items to be published onto.
data_roots:
  /neodc/obs4MIPs: /data/esg_obs4mips # As with the old publisher, "/neodc/obs4MIPs/" is replaced by "/data/esg_obs4mips" in the remote url path.
mountpoints:
verbose: false
silent: false
overrides:
  processing_code_location: 'undefined' # Can specify overrides to the attribute extraction, especially if the publisher-extracted values display as invalid/error.
exclusions:
  - license # To exclude a non-required property from the STAC record generated (use as needed if publisher-extracted values are invalid.)
project: obs4mips # Specify the esgvoc collection name (typically lowercase)
collection: obs4MIPs # Specify the STAC collection name (typically mixed-case)
access: HTTPS # Access method - for non-https create an issue in this repo as only HTTPS is supported.
stac_config:
  stac_transaction_api: 
    base_url: https://transaction-int.east.esgf.io
    scope_endpoint: https://transaction-int.east.esgf.io/scope
    timeout: 60
  token_storage_file: 'local/token.json'
```

The STAC configuration element handles EGI-check-in for user sign-in and generation of a local token file (valid for 30 days or less). The base-url and scope should be set to the correct transaction API (east/west and '-int' for staging):
- The records will be pushed to `transaction.<node>.esgf.io`
- The records will end up on `search.<node>.esgf.io`

## Special cases for config parameters

If the `data_node` does not resolve properly through the publisher (i.e there's some mistake with using esgf.<node>), you can override this by setting the value as `OVERRIDE:<your_service_path>` (E.g CEDA obs4MIPs data will use `dap.ceda.ac.uk` not `esgf.ceda.ac.uk`)

## Run the publisher

The command to run the publisher is:
```
esgvocpublish -cfg /path/to/yaml --map /path/to/mapfiles
```

Where you can also use flags:
 - `--dry-run` will not push the items to the STAC transaction API
 - `--save-stac` will save STAC records to a `local/` directory.