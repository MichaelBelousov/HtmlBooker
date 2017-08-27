import validators
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
from urllib.error import *
import sys
from html.parser import HTMLParser
from HtmlBooker import *

class DebugLinkFinder:
    def __init__(self, page):
        self.L = []
        self.graph = SiteGraph()
        self.origin = page
        self.homepage = page
        self.pages = [page]  # first element is homepage
        try:
            byteread = urlopen(page)
            content = byteread.read().decode('utf-8')
            ling = Swarmling(page, owner=self)
            ling.feed(content)
            ling.close()
        except Exception as e:
            print(e)
        for l in self.L: print(l)
    def spawn(self, page):
        if not validators.url(page):
            page = urljoin(self.homepage, page)
        if within_domain(page, self.homepage):
            self.L.append(page)
