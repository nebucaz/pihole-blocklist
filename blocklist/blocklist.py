#!/ust/bin/python
from datetime import datetime
from urllib.parse import urlparse, urlunparse
import re
import os
import sqlite3
import requests
import hashlib

# https://pythonawesome.com/a-console-progress-bar-module-for-python/
import enlighten

from requests.exceptions import Timeout, ConnectionError
from http.client import RemoteDisconnected
from os import path

from blocklist.models import Domain

class Blocklist():
    """
        Takes a list of URLs (one per line) as input. Tries to fetch the referenced file which should be a list of domains (one per line). Validates the domain builds a list of onique domains over all fetched files. At the end, exports a file with the unique domains of all the input lists. 
    """

    # list of blocklist-files
    adlist = None
    blockLists = []
    brokenLinks = []
    blockedDomains = []
    mydb_path = None
    

    def __init__(self, adlist = None, dbPath = None):
        super().__init__()
        self.adlist = adlist

        try:
            if path.exists(self.adlist):
                self.validateAdList()
            """
                with open(self.adlist) as fd:
                    self.adlist = fd.read()
            else:
                self.adlist = adlist

            if self.adlist != None:
                self.validateAdList()
            """
        except:
            print("no adlist to parse")

        self.mydb_path = ':memory:'
        if dbPath != None:
            self.mydb_path = dbPath
        self.initDB()

    def initDB(self):
        self.conn = None
    
        try:
            self.conn = sqlite3.connect(self.mydb_path)
            self.conn.row_factory = sqlite3.Row
            self.createTables()
        except sqlite3.Error as err:
            print("Error Connecting db: {}".format(self.mydb_path))
            print(err)

    def createTables(self):
        Domain.initDB(self.conn)

    def getBlacklistDomain(self, name):
        return Domain(db=self.conn).getByName(name)

    def validateAdList(self):
        self.brokenLinks.clear()
        self.blockLists.clear()

        try:
            with open(self.adlist) as list:
                for line in list:

                    # skip comments
                    if re.match('^\s*\#', line):
                        continue

                    parts = urlparse(line)
                    try:
                        if parts.netloc == '' or parts.scheme == '':
                            brokenLink = {"list": self.adlist, "url": line}
                            self.brokenLinks.append(brokenLink)
                            continue

                        self.blockLists.append(urlunparse(parts))
                    except Exception as e:
                        print(e)
        except IOError as e:
            print(e)
        except Exception as e:
            print(e)

    def updateDomains(self):
        try:
            for list in self.blockLists:
                print("fetching {}".format(list))

                lines = self.fetchList(list)
                lastH = self.getHash(list)
                newHash = self.makeHash(lines)
                if newHash != lastH:
                    self.writeHash(list, newHash)
                    self.parseList(lines, list)
                else:
                    print("no changes in list")

                #domains = self.parseList(lines)
                #self.storeDomainsFromList(domains, list)
        except:
            print("error while updating {}".format(list))

    # fetch a list 
    def fetchList(self, url):
        lines = None
        try:
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                lines = response.text
                self.makeHash(lines)
            else:
                print("status {} for {}".format(response.status_code, url))
        except (Timeout, RemoteDisconnected) as e:
            print("error while fetching {}".format(e))

        return lines

    def getHash(self, listUrl):
        hash = None
        hashFileName = self.hashFile(listUrl)
        try:
            with open(hashFileName, "r") as fh:
                hash = fh.readline()
        except:
            pass
        return hash

    def writeHash(self, list, hash):
        hashFileName = self.hashFile(list)
        with open(hashFileName, "w") as fh:
            fh.write(hash)

    def makeHash(self, lines):
        return hashlib.sha224(lines.encode('utf-8')).hexdigest()

    def hashFile(self, listUrl):
        url = urlparse(listUrl)
        return 'db/hash_' + url.hostname + url.path.replace('/', '_') + '.txt'

    # parse a list
    def parseList(self, lines, sourceList = None):
        domainList = []

        allLines = lines.splitlines()
        nLines = len(allLines)
        pbar = enlighten.Counter(total = nLines, desc='Parsing', unit='lines')
        for line in allLines:
            pbar.update()
            # skip comments
            if re.match('^\s*\#', line) or line == '' or line == None:
                continue
    
            try:
                sanitizedDomain = self.getDomain(line)
                if list != None:
                    #self.storeDomainUnique(sanitizedDomain)
                    self.storeDomainUnique(sanitizedDomain, sourceList, 0)
                else:
                    domainList.append(sanitizedDomain)
            except Exception as e: 
                print(e)

        return domainList

    # throws invalid url
    # line is one domain per line or in hosts-file format <ip-address> <domain> per line 
    def getDomain(self, line):
        parts = line.split(" ")
        if len(parts) > 1:
            return parts[1].strip()
        else:
            return line.strip()

    def storeDomainsFromList(self, domainList, url):
        try:
            for name in domainList:
                self.storeDomainUnique(name, url, 0)
        except:
            print("invalid domain list")

    # store the domain 
    def storeDomainUnique(self, domain, sourceList, status = 0):
        created = datetime.now().timestamp()
        exists = self.getBlacklistDomain(domain)
        if exists == None or exists.ID == 0:
            d = Domain(db=self.conn, name=domain, source=sourceList, created=created, status=status)
            d.save()
            #print("stored new entry: {}".format(domain))
            return d

        return exists