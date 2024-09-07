import sys, json, os, re
from esgcet.stac_client import TransactionClient
import argparse
from pathlib import Path
import esgcet.logger as logger
import esgcet.args as pub_args

log = logger.ESGPubLogger()
publog = log.return_logger('esgstacpub')

 
item_properties = {
    "CMIP6": [
        "version",
        "access",
        #"activity_drs",
        "activity_id",
        "cf_standard_name",
        "citation_url",
        #"data_node",
        "data_spec_version",
        #"dataset_id_template_",
        #"datetime_start",
        #"datetime_stop",
        #"directory_format_template_",
        "experiment_id",
        "experiment_title",
        "frequency",
        "further_info_url",
        #"north_degrees",
        #"west_degrees",
        #"south_degrees",
        #"east_degrees",
        #"geo",
        #"geo_units",
        "grid",
        "grid_label",
        #"height_bottom",
        #"height_top",
        #"height_units",
        #"index_node",
        #"instance_id",
        "institution_id",
        #"latest",
        #"master_id",
        #"member_id",
        #"metadata_format",
        "mip_era",
        "model_cohort",
        "nominal_resolution",
        #"number_of_aggregations",
        #"number_of_files",
        "pid",
        "product",
        "project",
        "realm",
        #"replica",
        #"size",
        "source_id",
        "source_type",
        "sub_experiment_id",
        "table_id",
        "title",
        #"type",
        #"url",
        "variable",
        "variable_id",
        "variable_long_name",
        "variable_units",
        "variant_label",
        #"xlink",
        #"_version_",
        "retracted",
        #"_timestamp",
        #"score",
    ]
}


def convert2stac(json_data):
    dataset_doc = {}
    for doc in json_data:
        if doc.get("type") == "Dataset":
            dataset_doc = doc
            break

    collection = dataset_doc.get("project")
    west_degrees = dataset_doc.get("west_degrees")
    south_degrees = dataset_doc.get("south_degrees")
    east_degrees = dataset_doc.get("east_degrees")
    north_degrees = dataset_doc.get("north_degrees")

    properties = {
        "start_datetime": dataset_doc.get("datetime_start"),
        "end_datetime": dataset_doc.get("datetime_end"),
    }
    property_keys = item_properties.get(collection)
    for k in property_keys:
        properties[k] = dataset_doc.get(k)

    item = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "extensions": [],
        "id": dataset_doc.get("instance_id"),
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [west_degrees, south_degrees],
                    [east_degrees, south_degrees],
                    [east_degrees, north_degrees],
                    [west_degrees, north_degrees],
                    [west_degrees, south_degrees]
                ]
            ]
        },
        "bbox": [
            [west_degrees, south_degrees, east_degrees, north_degrees]
        ],
        "collection": collection,
        "properties": properties,
    }

    assets = {}

    if "Globus" in dataset_doc.get("access"):
        for doc in json_data:
            if doc.get("type") == "File":
                urls = doc.get("url")
                for url in urls:
                    if url.startswith("globus:"):
                        m = re.search(r"^globus:([^/]*)(.*/)[^/]*$", url)
                        href = f"https://app.globus.org/file-manager?origin_id={m[1]}&origin_path={m[2]}"
                        assets = {
                            "globus": {
                                "href": href,
                                "description": "Globus Web App Link",
                                "type": "text/html",
                                "roles": ["data"],
                                "alternate:name": dataset_doc.get("data_node"),
                            }
                        }
                break

    if "HTTPServer" in dataset_doc.get("access"):
        counter = 0
        for doc in json_data:
            if doc.get("type") == "File":
                urls = doc.get("url")
                for url in urls:
                    if url.endswith("application/netcdf|HTTPServer"):
                        url_split = url.split("|")
                        href = url_split[0]
                        assets[f"data{counter:04}"] = {
                            "href": href,
                            "description": "HTTPServer Link",
                            "type": "application/netcdf",
                            "roles": ["data"],
                            "alternate:name": dataset_doc.get("data_node"),
                        }
                        counter += 1
                        break

    item["assets"] = assets

    return item


def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF STAC Transaction API.")

    home = str(Path.home())
    def_config = home + "/.esg/esg.yaml"
    parser.add_argument("--stac-api", dest="stac_api", default=None, help="Specify STAC Transaction API.")
    parser.add_argument("--pub-rec", dest="json_data", default=None,
                        help="JSON file output from esgpidcitepub or esgmkpubrec.")
    parser.add_argument("--config", "-cfg", dest="cfg", default=def_config, help="Path to yaml config file.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")
    pub = parser.parse_args()

    return pub


def run():
    a = get_args()

    ini_file = a.cfg
    if not os.path.exists(ini_file):
        publog.error("Config file not found. " + ini_file + " does not exist.")
        exit(1)
    if os.path.isdir(ini_file):
        publog.error("Config file path is a directory. Please use a complete file path.")
        exit(1)
    args = pub_args.PublisherArgs()
    config = args.load_config(ini_file)

    if not a.json_data:
        publog.error("Input data argument missing.  Please provide either records in .json form for esgf2 publishing")
        exit(1)

    if not a.silent:
        try:
            s = config['silent']
            if 'true' in s or 'yes' in s:
                silent = True
            else:
                silent = False
        except:
            silent = False
    else:
        silent = True

    if not a.verbose:
        try:
            v = config['verbose']
            if 'true' in v or 'yes' in v:
                verbose = True
            else:
                verbose = False
        except:
            verbose = False
    else:
        verbose = True


    rc = True
    tc = TransactionClient(a.stac_api, silent=silent, verbose=verbose)

    if a.json_data:
        try:
            new_json_data = json.load(open(a.json_data))
        except:
            publog.exception("Could not open json file. Exiting.")
            exit(1)
        try:
            stac_item = convert2stac(new_json_data)
            rc = rc and tc.publish(stac_item)
        except Exception as ex:
            publog.exception("Failed to publish to STAC Transaction API")
            exit(1)
    if not rc:
        exit(1)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()

