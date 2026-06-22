import pytest


from esgcet.esgf15.globus import ESGFGlobusIndex


marker_1000 = [
    "Q01JUDYuQWVyQ2hlbU1JUC5OQ0FSLkNFU00yLVdBQ0NNLmhpc3QtcGlOVENGLnIxaTJwMWYxLk9tb24uZGZlLmdyLnYyMDE5MDUzMXxlc2dmLW5vZGUub3JubC5nb3Y",
    "Q01JUDYuQWVyQ2hlbU1JUC5OQ0FSLkNFU00yLVdBQ0NNLmhpc3RTU1QucjFpMnAxZjEuQUVSbW9uLnVhLmduLnYyMDE5MDUzMXxlc2dmLW5vZGUub3JubC5nb3Y",
    "Q01JUDYuQWVyQ2hlbU1JUC5OQ0FSLkNFU00yLVdBQ0NNLnBpQ2xpbS1IQy5yMWkxcDFmMS5BRVJtb24ubW1yZHVzdC5nbi52MjAyMDAzMDJ8ZXNnZi1ub2RlLm9ybmwuZ292"
]

size_list = [3920, 5030, 3066]

def test_esgf15_globus():

    esgf_globus_index = ESGFGlobusIndex()

    fixed_facet = {'institution_id': 'NCAR'}

    result = esgf_globus_index.query_dataset_file('CMIP6', fixed_facet, 'esgf-node.ornl.gov', True, 1000)

    for k, res in enumerate(result):
        assert len(res) == 1000
        assert esgf_globus_index.marker == marker_1000[k]
        assert sum(len(nested) for nested in res) == size_list[k]


        for doc in res[k][1:]:
            assert doc["dataset_id"] == res[k][0]["id"]

        if k>1:
            break

