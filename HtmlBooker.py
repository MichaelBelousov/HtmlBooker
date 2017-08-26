import urllib, urllib.request
import sys
from html.parser import HTMLParser

# import plotly.plotly as ply
# from plotly.graph_objs import *
# import networkx as nx
# import matplotlib.pyplot as plt

class PageVertex: 
    """simple object wrapper for SiteGraph object"""
    def __init__(self):
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
        if tag == 'a' and hasattr(attrs, 'href'):
            self.handle_link(attrs.href)
        # return super().handle_starttag(tag, attrs)
    def handle_link(self, href):
        self.owner.graph.addEdge(self.page, href)
        self.owner.spawn(href)
    def handle_data(self, data):
        return super().handle_data(data)

class Swarm():
    """swarmling factory that recursively follows domain layout"""
    def __init__(self, homepage):
        super().__init__()
        self.graph = SiteGraph()
        self.pages = [homepage]  # first element is homepage
        self.run(homepage)
    def run(self, page):
        self.hardspawn(page)
        self.graph.compileVerts()
    def spawn(self, page):
        if page not in pages:
            pages.append(page)
            self.hardspawn(page)
    def hardspawn(self, page):
        byteread = urllib.request.urlopen(page)
        content = byteread.read().decode('utf-8')  # read and decode
        print(content, '\n' + 50* '=' +'\n')
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
