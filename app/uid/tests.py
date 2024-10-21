from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import CounterNode
from .models import Provider, LCVTerm, LanguageSet, UIDCounter, uid_generator # Import the UID generator from Models
#from .utils import generate_uid, issue_uid, send_notification
from .utils import send_notification
from django.urls import reverse
from rest_framework.test import APITestCase
from neomodel import db


class TestCounterNode(TestCase):
    @patch('app.uid.models.CounterNode.save')
    @patch('app.uid.models.CounterNode.nodes.first_or_none')
    def test_get_creates_counter_node_if_none(self, mock_first_or_none, mock_save):
        mock_first_or_none.return_value = None
        counter_node = CounterNode.get()
        mock_first_or_none.assert_called_once()
        mock_save.assert_called_once()
        self.assertEqual(counter_node.counter, 0)

    @patch('app.uid.models.CounterNode.create_node')
    @patch('app.uid.models.CounterNode.nodes.first_or_none')
    def test_get_returns_counter_node(self, mock_first_or_none, mock_create_node):
        mock_counter_node = MagicMock()
        mock_counter_node.counter = 1
        mock_first_or_none.return_value = mock_counter_node

        counter_node = CounterNode.get()

        mock_first_or_none.assert_called_once()

        mock_create_node.assert_not_called()

        self.assertEqual(counter_node.counter, 1)
    
    
    @patch('app.uid.models.CounterNode.save')
    def test_create_node(self, mock_save):
        counter_node = CounterNode.create_node()
        mock_save.assert_called_once()
        self.assertEqual(counter_node.counter, 0)
    
    @patch('app.uid.models.CounterNode.save')
    @patch('app.uid.models.CounterNode.get')
    def test_increment(self, mock_get, mock_save):
        mock_counter_node = MagicMock()
        mock_counter_node.counter = 1
        mock_get.return_value = mock_counter_node

        counter_node = CounterNode.increment()

        mock_get.assert_called_once()
        self.assertEqual(counter_node.counter, 2)
        mock_save.assert_called_once()

class UIDGenerationTestCase(TestCase):

    def setUp(self):
        UIDCounter.objects.all().delete()  # Ensure a clean state before each test

    def test_uid_generation_for_providers(self):
        provider = Provider.objects.create(name="Test Provider")
        self.assertIsNotNone(provider.uid)
        self.assertTrue(provider.uid.startswith("0x"))
        self.assertEqual(len(provider.uid), 10)  # Assuming UID length is 10 (0x + 8 hex digits)
        self.assertNotIn(provider.uid, [p.uid for p in Provider.objects.all() if p.uid])

    def test_uid_generation_for_lcv_terms(self):
        lcv_term = LCVTerm.objects.create(term="Test LCV Term")
        self.assertIsNotNone(lcv_term.uid)
        self.assertTrue(lcv_term.uid.startswith("0x"))
        self.assertEqual(len(lcv_term.uid), 10)  # Assuming UID length is 10 (0x + 8 hex digits)
        self.assertNotIn(lcv_term.uid, [l.uid for l in LCVTerm.objects.all() if l.uid])

    def test_uid_generation_for_language_sets(self): #Changes to reflect LanguageSet now DjangoNode
        with db.transaction:
            #language_set = LanguageSet.objects.create(name="Test Language Set")
            language_set = LanguageSet(name="Test Language Set").save()
            self.assertIsNotNone(language_set.uid)
            self.assertTrue(language_set.uid.startswith("0x"))
            self.assertEqual(len(language_set.uid), 10)  # Assuming UID length is 10 (0x + 8 hex digits)
            self.assertNotIn(language_set.uid, [ls.uid for ls in LanguageSet.objects.all() if ls.uid])

    def test_issuing_uid_to_providers(self):
        provider = Provider.objects.create(name="Test Provider")
        self.assertIsNotNone(provider.uid)
        self.assertTrue(provider.uid.startswith("0x"))
        self.assertEqual(provider.uid, uid_generator.generate_uid())

    def test_issuing_uid_to_lcv_terms(self):
        lcv_term = LCVTerm.objects.create(term="Test LCV Term")
        self.assertIsNotNone(lcv_term.uid)
        self.assertTrue(lcv_term.uid.startswith("0x"))
        self.assertEqual(lcv_term.uid, uid_generator.generate_uid())

    def test_verification_of_uid_assignment(self):
        provider = Provider.objects.create(name="Test Provider")
        lcv_term = LCVTerm.objects.create(term="Test LCV Term")
        self.assertEqual(provider.uid, uid_generator.generate_uid())
        self.assertEqual(lcv_term.uid, uid_generator.generate_uid())

    def test_notification_on_successful_uid_issuance(self):
        provider = Provider.objects.create(name="Test Provider")
        lcv_term = LCVTerm.objects.create(term="Test LCV Term")
        provider_uid = provider.uid
        lcv_term_uid = lcv_term.uid
        self.assertTrue(send_notification(provider, provider_uid))
        self.assertTrue(send_notification(lcv_term, lcv_term_uid))
class ExportToPostmanTestCase(APITestCase):

    def test_export_provider(self):
        provider = Provider.objects.create(name="Test Provider", uid="P-1234567890")
        url = reverse('export_to_postman', args=[provider.uid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['uid'], provider.uid)

    def test_export_lcv_term(self):
        lcv_term = LCVTerm.objects.create(name="Test LCV Term", uid="L-1234567890")
        url = reverse('export_to_postman', args=[lcv_term.uid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['uid'], lcv_term.uid)

    def test_export_invalid_uid(self):
        url = reverse('export_to_postman', args=["invalid-uid"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)