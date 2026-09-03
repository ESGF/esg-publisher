
from enum import Enum
import json

from globus_sdk import (
    SearchClient,
    SearchScrollQuery,
    SearchQueryV1,

)
from typing import Any, Literal, Generator

from collections import defaultdict

class Project(str, Enum):

    """read-only projects."""
    CMIP3 = "CMIP3"
    CMIP5 = "CMIP5"
    CMIP6 = "CMIP6"
    CREATETP = "CREATE-IP"
    E3SMSUPPL = "e3sm-supplement"
    GEOMIP = "GeoMIP"
    LUCID = "LUCID"
    TAMIP = "TAMIP"
    GFDL_CMIP6 = "GFDL-CMIP6"
    GFDL_CMIP5 = "GFDL-CMIP5"
    GFDL_LLNL_CMIP6 = "GFDL-LLNL-CMIP6"
    GFDL_LLNL_CMIP5 = "GFDL-LLNL-CMIP5"

    """read-write projects."""
    CMIP6PLUS = "CMIP6Plus"
    DRCDP = "DRCDP"
    E3SM = "e3sm"
    INPUT4MIPS = "input4MIPs"
    OBS4MIPS = "obs4MIPs"
    WRPMIP = "WrPMIP"



class ESGFGlobusIndex:

    ESGF_Globus_Index = {
        "ESGF2-US-1.5-Catalog": "a8ef4320-9e5a-4793-837b-c45161ca1845"
    }

    """ class for ESGF Globus Index """

    def __init__(
        self,
        globus_index_name:str = "ESGF2-US-1.5-Catalog"

    ) -> None:

        if globus_index_name in self.ESGF_Globus_Index:
            self.index_id = self.ESGF_Globus_Index[globus_index_name]
        else:
            raise ValueError("the index is not supported")
 
        self.query_client = SearchClient()
        self.marker = None

    @staticmethod
    def _generate_query_dict(
        meta_type: Literal['File', 'Dataset'],
        project: Project,
        fixed_facet: dict[str, Any],
        data_node: str,
        is_replica: bool = False,
    ) -> dict[str, Any]:
        
        query_dict= {"filters":[]}
        for key, val in fixed_facet.items():
            query_dict["filters"].append({
                "field_name": key,
                "values": val if isinstance(val, list) else [val],
                "type": "match_all",
            })

        query_dict["filters"].append(
            {
                "field_name": 'data_node',
                "values": [data_node],
                "type": "match_all",
            }
        )

        query_dict["filters"].append(
            {
                "field_name": 'project',
                "values": [project.value],
                "type": "match_all",
            }
        )

        query_dict["filters"].append(
            {
                "field_name": 'type',
                "values": [meta_type],
                "type": "match_all",
            }
        )

        query_dict["filters"].append(
            {
                "field_name": "replica",
                "values": [is_replica],
                "type": "match_all",
            }
        )


        return query_dict


    def query_dataset_file(
        self, 
        project: Project, 
        fixed_facet: dict[str, Any],
        data_node: str,
        is_replica: bool = False,
        dataset_limit: int = 1000,
    ) -> Generator[list[list[dict[str, Any]]], None, None]:
        """query index using project and a fixed_facet"""

        
        query_dict_dset = self._generate_query_dict(
            'Dataset', 
            project, 
            fixed_facet, 
            data_node, 
            is_replica,
        )
        query_str = SearchScrollQuery(limit=dataset_limit, additional_fields=query_dict_dset)
        paginator = self.query_client.paginated.scroll(self.index_id, query_str) 

        query_dict_file = self._generate_query_dict(
            'File',
            project,
            fixed_facet,
            data_node,
            is_replica,
        )

        query_dict_file["sort"] = [
            {
                "field_name": "id",
                "order": "asc"
            }
        ]

        for response in paginator:

            if response.data['total'] == 0:
                raise ValueError(
                    "Cannot find any dataset using the query filter:\n"
                    f"{json.dumps(query_dict_dset)}"
                )

            self.marker = response.data.get('marker')
            result_dict = defaultdict(list)
            dataset_ids = []
            for g in response.data["gmeta"]:
                dataset_ids.append(g["subject"])
                result_dict[g["subject"]] = [g["entries"][0]["content"]]

            query_dict_file["filters"].append(
                {
                    "field_name": "dataset_id",
                    "values": dataset_ids,
                    "type": "match_any",
                },
            )

            search_result = self.query_client.post_search(
                self.index_id, 
                SearchQueryV1(
                    limit=10000,
                    offset =0,
                    filters=query_dict_file["filters"],
                    sort=query_dict_file["sort"]
                )
            )

            del query_dict_file["filters"][-1]

            if search_result["total"] > 10000:
                raise ValueError("Over Globus post search limit, reduce the limit_dataset")

            for gmeta in search_result["gmeta"]:
                ds_id = gmeta["entries"][0]["content"]["dataset_id"]
                result_dict[ds_id].append(gmeta["entries"][0]["content"])

            yield list(result_dict.values())
