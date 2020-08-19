# To contain at least a success and failure test for each function in the utils directory
import unittest

try:
    import esgf.publisher as publisher
except:
    import utils.wrap_esgf_publisher as publisher

import utils.verify as verify
import utils.datasets as d
from utils.info_classes import (
    ESGFPublicationVerificationError, ESGFPublicationTestError)

good_dataset = good = d.d1v1
bad_dataset = bad = d.d3v1

class UtilsTests(unittest.TestCase):

    def setUp(self):
        # To tests our verify utilities we need to publish
        publisher.publish(good.id, good.files)

    def tearDown(self):
        # Unpublish all after tests complete
        publisher.unpublish(good.id, good.files)

    def test_get_all_verify_funcs_all(self):
        self.assertEqual(verify.get_all_verify_funcs(),
            (verify.verify_files_on_disk, verify.verify_published_to_db,
             verify.verify_published_to_tds, verify.verify_published_to_solr))

    def test_get_all_verify_funcs_single_arg(self):
        self.assertEqual(verify.get_all_verify_funcs("solr"),
            (verify.verify_published_to_solr,))

    def test_fails_get_all_verify_funcs(self):
        self.assertRaises(Exception, verify.get_all_verify_funcs, ("disk", "nonsense",))

    def test_get_file_list(self):
        resp = verify.get_file_list(good.id)
        self.assertEqual(resp, good.files)

    def test_fails_get_file_list(self):
        self.assertRaises(ESGFPublicationTestError, verify.get_file_list,
                          (bad.id,))

    def test_verify_files_on_disk(self):
        verify.verify_files_on_disk(good.id, good.files)

    def test_fails_verify_files_on_disk(self):
        self.assertRaises(ESGFPublicationVerificationError, verify.verify_files_on_disk,
                          (bad.id, bad.files))

    def test_verify_published_to_db(self):
        verify.verify_published_to_db(good.id, good.files)

    def test_fails_verify_published_to_db(self):
        self.assertRaises(ESGFPublicationVerificationError, verify.verify_published_to_db,
                          (bad.id, bad.files))

    def test_verify_published_to_tds(self):
        verify.verify_published_to_tds(good.id, good.files)

    def test_fails_verify_published_to_tds(self):
        self.assertRaises(ESGFPublicationVerificationError, verify.verify_published_to_db,
                          (bad.id, bad.files))

    def test_verify_published_to_solr(self):
        verify.verify_published_to_solr(good.id, good.files)

    def test_fails_verify_published_to_solr(self):
        self.assertRaises(ESGFPublicationVerificationError, verify.verify_published_to_db,
                          (bad.id, bad.files))

    def test_verify_dataset_published(self):
        verify.verify_dataset_published(good.id)

    def test_fails_verify_dataset_published(self):
        self.assertRaises(ESGFPublicationVerificationError, verify.verify_dataset_published,
                          (bad.id,))

if __name__ == "__main__":

    unittest.main()