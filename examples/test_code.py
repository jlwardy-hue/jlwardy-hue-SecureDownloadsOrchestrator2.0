import unittest
from datetime import datetime

class TestStringMethods(unittest.TestCase):
    """Test cases for string manipulation functions."""
    
    def test_upper(self):
        """Test string upper() method."""
        self.assertEqual('foo'.upper(), 'FOO')
        
    def test_isupper(self):
        """Test string isupper() method."""
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())
        
    def test_split(self):
        """Test string split() method."""
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        
    def setUp(self):
        """Set up test fixtures."""
        self.test_string = "Hello, World!"
        self.timestamp = datetime.now()

if __name__ == '__main__':
    unittest.main()
