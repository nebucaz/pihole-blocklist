import unittest
from datetime import datetime
from sqlite3 import Error
from os import path, remove

from blocklist.blocklist import Blocklist
from blocklist.models import Domain


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
    def test_invalidURLs(self):
        blocklist = Blocklist("blocklist/tests/lists/invalid.list")
        self.assertIsNotNone(blocklist.adlist)
        blocklist.validateAdList()
        self.assertTrue(blocklist.blockLists)
        self.assertEqual(1, len(blocklist.blockLists))

    def test_loadAdList(self):
        blocklist = Blocklist("blocklist/tests/lists/adlist.list")
        self.assertIsNotNone(blocklist.adlist)
        blocklist.validateAdList()

    def test_parseList(self):
        blocklist = Blocklist()
        domainList = blocklist.parseList("unique.com\nsalsa.de\nrumba.br\n")
        self.assertTrue(domainList)
        self.assertEqual(3, len(domainList))

    def test_getDomain(self):
        blocklist = Blocklist()
        domain = blocklist.getDomain("127.0.0.1 unique.com")
        self.assertEqual("unique.com", domain)
        domain2 = blocklist.getDomain("adjust.io")
        self.assertEqual("adjust.io", domain2)

    def test_DomainModel(self):
        name = "unique.com"
        blocklist = Blocklist()
        d = Domain(db = blocklist.conn, name=name, created = datetime.now().timestamp(), status=0, source= "blabla")
        d.save()

        cur = blocklist.conn.cursor()
        cur.execute("SELECT * FROM `blacklist` WHERE `DomainName` = ?", [name])
        domain = cur.fetchone()
        self.assertIsNotNone(domain)
        self.assertEqual(name, domain['DomainName'])

        domain2 = Domain(db=blocklist.conn).getByName("unique.com")
        self.assertIsNotNone(domain2)
        self.assertEqual(name, domain2.DomainName)

    def test_databaseFile(self):
        if path.exists("db/test.db"):
            remove("db/test.db")
    
        blocklist = Blocklist(dbPath="db/test.db")
        self.assertTrue(path.exists("db/test.db"))

    def test_storeUnique(self):
        name = "unique.com"
        blocklist = Blocklist()
        blocklist.storeDomainUnique(name, sourceList="a")
        blocklist.storeDomainUnique(name, sourceList="b")

        cur = blocklist.conn.cursor()
        cur.execute("SELECT count(*) FROM `blacklist` WHERE `DomainName` = ?", [name])
        count = cur.fetchone()[0]
        self.assertEqual(1, count)

    def test_fetchList(self):
        blocklist = Blocklist()
        lines = blocklist.fetchList("https://s3.amazonaws.com/lists.disconnect.me/simple_tracking.txt")
        self.assertIsNotNone(lines)
        domainList = blocklist.parseList(lines)
        self.assertEqual(34, len(domainList))

    def test_storeDomainsFromList(self):
        blocklist = Blocklist() #Blocklist(dbPath="db/test.db")
        blocklist.conn.execute("delete from blacklist")
        lines = blocklist.fetchList("https://s3.amazonaws.com/lists.disconnect.me/simple_tracking.txt")
        self.assertIsNotNone(lines)
        domainList = blocklist.parseList(lines)
        blocklist.storeDomainsFromList(domainList, "https://s3.amazonaws.com/lists.disconnect.me/simple_tracking.txt")

        cur = blocklist.conn.cursor()
        cur.execute("select count(*) from blacklist")
        count = cur.fetchone()[0]
        self.assertEqual(len(domainList), count)
