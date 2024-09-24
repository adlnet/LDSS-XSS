from django.test import TestCase
from unittest.mock import patch, MagicMock
from .models import CounterNode

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
