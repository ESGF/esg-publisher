import re

from esgcet.settings import STAC_API

item_properties = {
    "CMIP6": [
        "version",
        "access",
        # "activity_drs",
        "activity_id",
        "cf_standard_name",
        # "citation_url",
        # "data_node",
        # "data_specs_version",
        # "dataset_id_template_",
        # "datetime_start",
        # "datetime_stop",
        # "directory_format_template_",
        "experiment_id",
        "experiment_title",
        "frequency",
        "further_info_url",
        # "north_degrees",
        # "west_degrees",
        # "south_degrees",
        # "east_degrees",
        # "geo",
        # "geo_units",
        "grid",
        "grid_label",
        # "height_bottom",
        # "height_top",
        # "height_units",
        # "index_node",
        # "instance_id",
        "institution_id",
        # "latest",
        # "master_id",
        # "member_id",
        # "metadata_format",
        "mip_era",
        "model_cohort",
        "nominal_resolution",
        # "number_of_aggregations",
        # "number_of_files",
        # "pid",
        "product",
        "project",
        "realm",
        # "replica",
        # "size",
        "source_id",
        "source_type",
        "sub_experiment_id",
        "table_id",
        "title",
        # "type",
        # "url",
        "variable",
        "variable_id",
        "variable_long_name",
        "variable_units",
        "variant_label",
        # "xlink",
        # "_version_",
        "retracted",
        # "_timestamp",
        # "score",
    ]
}


def convert2stac(json_data):
    dataset_doc = {}
    for doc in json_data:
        if doc.get("type") == "Dataset":
            dataset_doc = doc
            break

    collection = dataset_doc.get("project")
    item_id = dataset_doc.get("instance_id")
    west_degrees = dataset_doc.get("west_degrees", 0.0)
    south_degrees = dataset_doc.get("south_degrees", -90.0)
    east_degrees = dataset_doc.get("east_degrees", -360.0)
    north_degrees = dataset_doc.get("north_degrees", 90.0)

    properties = {
        "datetime": None,
        "start_datetime": dataset_doc.get("datetime_start", "1975-01-01T00:00:00Z"),
        "end_datetime": dataset_doc.get("datetime_end", "1975-01-02T00:00:00Z"),
    }
    property_keys = item_properties.get(collection)
    for k in property_keys:
        properties[k] = dataset_doc.get(k)

    item = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "extensions": [
            "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json"
        ],
        "id": item_id,
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [west_degrees, south_degrees],
                    [east_degrees, south_degrees],
                    [east_degrees, north_degrees],
                    [west_degrees, north_degrees],
                    [west_degrees, south_degrees],
                ]
            ],
        },
        "bbox": [west_degrees, south_degrees, east_degrees, north_degrees],
        "collection": collection,
        "links": [
            {
                "rel": "self",
                "type": "application/json",
                "href": f"{STAC_API}/collections/{collection}/items/{item_id}",
            },
            {
                "rel": "parent",
                "type": "application/json",
                "href": f"{STAC_API}/collections/{collection}",
            },
            {
                "rel": "collection",
                "type": "application/json",
                "href": f"{STAC_API}/collections/{collection}",
            },
            {
                "rel": "root",
                "type": "application/json",
                "href": f"{STAC_API}/collections",
            },
        ],
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
