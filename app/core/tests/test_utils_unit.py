from unittest.mock import patch

from ddt import data, ddt, unpack
from django.test import tag

from ..management.utils.signals_utils import (create_child_termset,
                                              create_terms, term_object,
                                              termset_object, update_status)
from ..management.utils.xss_helper import bleach_data_to_json, sort_version
from ..models import ChildTermSet, TermSet
from .test_setup import TestSetUp


@tag('unit')
@ddt
class UtilsTests(TestSetUp):

    def test_create_child_termset(self):
        """Test function creating child termsets"""
        self.termset.save()
        termset_name = 'test1'
        termset = TermSet.objects.get(name=self.schema_name)
        return_val = create_child_termset(termset_name, termset,
                                          self.status, self.user)

        self.assertEqual(return_val.parent_term_set, termset)
        self.assertEqual(return_val.name, termset_name)
        self.assertEqual(return_val.status, self.status)

    def test_create_terms(self):
        """Test function to create/save terms"""
        self.termset.save()
        termset = TermSet.objects.get(name=self.schema_name)
        return_val = create_terms(self.metadata["test"]["test1"], "test1",
                                  termset, self.status, self.user)

        self.assertEqual(return_val.term_set, termset)
        self.assertEqual(return_val.name, "test1")
        self.assertEqual(return_val.use, "Required")
        self.assertEqual(return_val.type, "int")

    @data(({'key': {'key1': {'key2': 'val'}}}, {'key1': {'key2': 'val'}}))
    @unpack
    def test_save_metadata(self, data1, data2):
        """Test Function to flatten/normalize data dictionary"""
        with patch('core.management.utils.signals_utils.'
                   'create_child_termset') as mock_create_child_termset, \
                patch('core.management.utils.signals_utils.'
                      'termset_object') as mock_termset_object, \
                patch('core.management.utils.'
                      'signals_utils.term_object') as mock_term_object:
            termset_object(data1, self.schema_iri, self.status, self.user)

            self.assertEqual(mock_create_child_termset.call_count, 1)
            self.assertEqual(mock_termset_object.call_count, 1)

            termset_object(data2, self.schema_iri, self.status, self.user)

            self.assertEqual(mock_term_object.call_count, 1)

    def test_term_object(self):
        """Test function to update flattened object to dict variable"""
        with patch('core.management.utils.signals_utils.'
                   'create_terms') as mock_create_terms:
            term_object('term_obj', 'term_name', 'parent_iri',
                        'status', self.user)
            self.assertEqual(mock_create_terms.call_count, 1)

    def test_update_status(self):
        """Test function to update the status of children terms/termsets"""
        self.schema.save()
        termset = TermSet.objects.get(name='test_name')
        update_status(termset, "Retired", self.user)
        child_termset = ChildTermSet.objects.get(parent_term_set=termset)

        self.assertEqual(child_termset.status, "Retired")

    def test_sort_version(self):
        """Test function to sort TermSets by version"""
        one = TermSet(name="one", version="1.1.1")
        two = TermSet(name="two", version="2.2.2")
        three = TermSet(name="three", version="2.2.3")
        ts_list = [one, three, two]

        sort_version(ts_list, reverse_order=True)
        self.assertEqual(ts_list, [three, two, one])

        sort_version(ts_list)
        self.assertEqual(ts_list, [one, two, three])

    def test_bleach(self):
        """Test function to bleach dicts"""
        html = "<em>test</em></br>string"
        clean = "teststring"

        bad_dict = {'outer': {'inner': html}}
        clean_dict = {'outer': {'inner': clean}}

        returned_dict = bleach_data_to_json(bad_dict)

        self.assertEqual(returned_dict, bad_dict)
        self.assertDictEqual(clean_dict, returned_dict)
