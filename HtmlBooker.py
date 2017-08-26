from urllib.request import urlopen
from urllib.parse import urljoin
import sys
from html.parser import HTMLParser

# import plotly.plotly as ply
# from plotly.graph_objs import *
# import networkx as nx
# import matplotlib.pyplot as plt

class PageVertex: 
    """simple object wrapper for SiteGraph object"""
    def __init__(self, obj):
        self.obj = obj
        self.nbrs = set()
    def addNbr(self, nbr):
        self.nbrs.add(nbr) 

class SiteGraph:
    """a directed graph of a domain's hyper links, ignoring
    external links"""
    def __init__(self):
        self.vertices = []
        self.edges = []
    def addEdge(self, edge):
        """add a 2-tuple of vertices that exist in the graph"""
        assert len(edge) == 2
        for e in edge:
            if e not in self.vertices:
                self.addVertex(e)
        self.edges.append(edge)
    def addVertex(self, vertex):
        """wrap any object as a vertex"""
        vertex = PageVertex(vertex)
        self.vertices.append(vertex)
    def compileVerts(self):
        """compiles vertex info"""
        for v in self.vertices:
            for e in (e for e in self.edges if e[0] is v ):
                v.addNbr(e[1])
    def inSequence(self, vertex):
        """detects whether a vertex is part of an independent page sequence"""
        pass  # return bool

class Swarmling(HTMLParser):
    """html page processor from the swarm"""
    def __init__(self, page, owner=None):
        assert owner is not None
        self.owner = owner
        self.page = page
        self.reset()
        super().__init__()
    def handle_starttag(self, tag, attrs):
        # convert attrs to dict to support attribute mapping;
        # for links this should be fine, but some attributes
        # might have multiple values
        attrs = {k:v for k,v in attrs}
        if tag == 'a' and 'href' in attrs:
            self.handle_link(attrs['href'])
        # return super().handle_starttag(tag, attrs)
    def handle_link(self, href):
        self.owner.graph.addEdge( (self.page, href) )
        self.owner.spawn(href)
    def handle_data(self, data):
        super().handle_data(data)

class Swarm():
    """swarmling factory that recursively follows domain layout"""
    def __init__(self, homepage):
        super().__init__()
        self.graph = SiteGraph()
        self.homepage = homepage
        self.pages = [homepage]  # first element is homepage
        self.run(homepage)
    def run(self, page):
        print('RUN>', page)
        self._spawn(page)
        self.graph.compileVerts()
    def spawn(self, page):
        # IDEA: Create a set of webpages which has a domain,
        # and can resolve absolute and relative URLs identically
        page = urljoin(self.homepage, page)
        if page not in self.pages:
            print('SPAWN>',page)
            self.pages.append(page)
            self._spawn(page)
    def _spawn(self, page):
        byteread = urlopen(page)
        content = byteread.read().decode('utf-8')  # read and decode
        # print(content, '\n' + 50* '=' +'\n')
        ling = Swarmling(page, owner=self)
        ling.feed(content)
        ling.close()

def main(args):
    if len(args) != 2:
        raise Exception('Too many arguments passed to the script')
    target = args[1]
    s = Swarm(target)
    # G = nx.DiGraph()
    # G.add_nodes_from(s.graph.vertices)
    # G.add_edges_from(s.graph.edges)
    # nx.draw(G)
    # nx.draw_shell(G)
    # plt.show()
    print('pages: ', s.pages)
    print('edges: ', s.graph.edges)
    print('verts: ', s.graph.vertices)

if __name__ == '__main__':
    main(sys.argv)
