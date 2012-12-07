import unittest
from vaurien.util import chunked


class TestUtil(unittest.TestCase):

    def test_chunked(self):
        self.assertEqual(sum(list(chunked(7634, 2049))), 7634)
