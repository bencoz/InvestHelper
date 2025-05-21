import unittest
from unittest.mock import patch
import sys
# Add the project root to the Python path to allow importing project modules
sys.path.insert(0, sys.path[0] + "/..")
from io_utils import query_yes_no

class TestQueryYesNo(unittest.TestCase):

    @patch('builtins.input')
    def test_yes_inputs(self, mock_input):
        # Test 'yes'
        mock_input.return_value = 'yes'
        self.assertTrue(query_yes_no("Test question?"))
        # Test 'y'
        mock_input.return_value = 'y'
        self.assertTrue(query_yes_no("Test question?"))
        # Test 'YES'
        mock_input.return_value = 'YES'
        self.assertTrue(query_yes_no("Test question?"))
        # Test 'Y'
        mock_input.return_value = 'Y'
        self.assertTrue(query_yes_no("Test question?"))

    @patch('builtins.input')
    def test_no_inputs(self, mock_input):
        # Test 'no'
        mock_input.return_value = 'no'
        self.assertFalse(query_yes_no("Test question?"))
        # Test 'n'
        mock_input.return_value = 'n'
        self.assertFalse(query_yes_no("Test question?"))
        # Test 'NO'
        mock_input.return_value = 'NO'
        self.assertFalse(query_yes_no("Test question?"))
        # Test 'N'
        mock_input.return_value = 'N'
        self.assertFalse(query_yes_no("Test question?"))

    @patch('builtins.input')
    def test_default_yes(self, mock_input):
        # Test default 'yes' when user enters nothing
        mock_input.return_value = ''
        self.assertTrue(query_yes_no("Test question?", default="yes"))

    @patch('builtins.input')
    def test_default_no(self, mock_input):
        # Test default 'no' when user enters nothing
        mock_input.return_value = ''
        self.assertFalse(query_yes_no("Test question?", default="no"))

    @patch('builtins.input')
    def test_default_none_requires_input(self, mock_input):
        # Test default 'None', ensuring it prompts until valid input
        # First attempt empty, second 'yes'
        mock_input.side_effect = ['', 'yes']
        # We need to also mock sys.stdout to suppress print output during test
        with patch('sys.stdout'):
            self.assertTrue(query_yes_no("Test question?", default=None))
        # Check that input was called twice
        self.assertEqual(mock_input.call_count, 2)

    @patch('builtins.input')
    def test_invalid_then_valid_input(self, mock_input):
        # Test invalid input then valid input
        mock_input.side_effect = ['maybe', 'y']
        with patch('sys.stdout'): # Suppress "Please answer..."
            self.assertTrue(query_yes_no("Test question?", default="no"))
        self.assertEqual(mock_input.call_count, 2)

    def test_invalid_default_value(self):
        with self.assertRaises(ValueError):
            query_yes_no("Test question?", default="maybe")

if __name__ == '__main__':
    unittest.main()
