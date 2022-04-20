import unittest
from blocklist.blocklist import Blocklist

class FetcherTest(unittest.TestCase):
    def test_loadEmptyList(self):
        blocklist = Blocklist()
        self.assertFalse(blocklist.blockLists)
        blocklist.validateAdList()
        self.assertFalse(blocklist.blockLists)
    
    def test_ignoreComments(self):
        blocklist = Blocklist("blocklist/tests/lists/comments.list")
        self.assertIsNotNone(blocklist.adlist)
        blocklist.validateAdList()
        self.assertEqual(1, len(blocklist.blockLists))
    
    # test list with invalid, not found entries

    def test_loadAdList(self):
        blocklist = Blocklist("blocklist/tests/lists/adlist.list")
        self.assertIsNotNone(blocklist.adlist)
        blocklist.validateAdList()
