from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import CCVTerm, LCVTerm

# Create your tests here.

@patch('uid.models.ProviderDjangoModel.ensure_provider_exists')
@patch('uid.models.UIDNode.create_node')
class TestCCVTerm(TestCase):
    def test_create_node_with_ccvid(self, mock_ensure_provider_exists, mock_create_uid_node):
        mock_uid_node = MagicMock()
        mock_uid_node.uid = '0x0000000'
        mock_create_uid_node.return_value = mock_uid_node

        mock_provider = MagicMock()
        mock_provider.default_uid = '0x0000000'
        mock_ensure_provider_exists.return_value = mock_provider

        ccv_term = CCVTerm.create_node(ccvid='0x0000000')

        self.assertEqual(ccv_term.ccvid, '0x0000000')
        self.assertEqual(ccv_term.uid_chain, '0x0000000-0x0000000')




