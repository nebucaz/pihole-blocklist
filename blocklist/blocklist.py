#!/ust/bin/python
from urllib.parse import urlparse
import re

class Blocklist():
    """
        Takes a list of URLs (one per line) as input. Tries to fetch the referenced file which should be a list of domains (one per line). Validates the domain builds a list of onique domains over all fetched files. At the end, exports a file with the unique domains of all the input lists. 
    """

    # list of blocklist-files
    adlist = None
    blockLists = []

    def __init__(self, adlist = None):
        super().__init__()

        self.adlist = adlist

    def validateAdList(self):
        try:
            with open(self.adlist) as list:
                for line in list:

                    # skip comments
                    if re.match('^\s*\#', line):
                        continue

                    url = urlparse(line)
                    try:
                        if url.netloc == None or url.scheme == None:
                            continue

                        self.blockLists.append(url)
                    except Exception as e:
                        print(e)
        except IOError as e:
            print(e)
        except Exception as e:
            print(e)