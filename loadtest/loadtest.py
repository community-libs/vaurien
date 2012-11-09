import json
import re
import random
import unicodedata

from funkload.FunkLoadTestCase import FunkLoadTestCase


class VaurienTest(FunkLoadTestCase):

    def __init__(self, *args, **kwargs):
        super(VaurienTest, self).__init__(*args, **kwargs)
        self.root = self.conf_get('main', 'url')

    def test_vaurien(self):
        res = self.get(self.root)
        self.assert_(res.code == 200)


if __name__ == '__main__':
    import unittest
    unittest.main()
