import validators
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
from urllib.error import *
import sys
from html.parser import HTMLParser
from weakref import ref

def almost(iter, key=lambda t: t, percent=0.8):
    """this is a pile of horse crock"""
    assert percent <= 1 and percent >= 0
    l = [bool(key(i)) for i in iter]
    return sum(l)/len(l) > percent 

def within_domain(site, domain):
    return (validators.url(site) and validators.url(domain) and 
            urlparse(site).netloc == urlparse(domain).netloc)

class PageVertex: 
    """simple object wrapper for SiteGraph object"""
    def __init__(self, obj, owngraph):
        self.obj = obj
        self.owngraph = ref(owngraph)
        self.nbrs = []
    def addNbr(self, nbr):
        if nbr not in self.nbrs:
            self.nbrs.append(nbr) 
    def sequential(self):
        """returns true if the vertex in its graph forms
        a unique sequence of edges with other vertices"""
        verts = self.owngraph().vertices.copy()
        verts.remove(self)
        return len([v for v in verts if v in self.nbrs])
        # return not almost( (v in self.nbrs for v in verts) )
    def __eq__(self, other):
        return str(self) == str(other) 
    def __str__(self):
        return str(self.obj)
    def __repr__(self):
        return repr(self.obj)
    def __hash__(self):
        return hash(self.obj)

class SiteGraph:
    """a directed graph of a domain's hyper links, ignoring
    external links"""
    def __init__(self):
        self.vertices = []  # rename to verts
        self.edges = []
    def add_edge(self, edge):
        """add a 2-tuple of vertices that exist in the graph"""
        assert len(edge) == 2
        for e in edge:
            if e not in self.vertices:
                self.add_vertex(e)
        if edge not in self.edges:
            self.edges.append(edge)
    def add_vertex(self, vertex):
        """wrap any object as a vertex"""
        vertex = PageVertex(vertex, self)
        self.vertices.append(vertex)
    def compile_verts(self):
        """compiles vertex info"""
        for v in self.vertices:
            for e in (e for e in self.edges if e[0] is v ):
                v.addNbr(e[1])
    # TODO: switch to underlined naming_scheme from camelcase namingScheme
    def sequential_verts(self):
        """checks the entire graph for all sequential vertices"""
        result = {}
        for v in self.vertices:
            result[v] = v.sequential()
        return result
            
class Swarmling(HTMLParser):
    """html page processor from the swarm"""
    def __init__(self, page, owner=None):
        assert owner is not None
        self.owner = ref(owner)
        self.page = page
        self.reset()
        super().__init__()
    def handle_starttag(self, tag, attrs):
        # convert attrs to dict to support attribute mapping;
        # for links this should be fine, but some attributes
        # might have multiple values
        # TODO: ignore URLs like "mailto:"
        attrs = {k:v for k,v in attrs}
        if tag == 'a' and 'href' in attrs:
            # if the URL is local, it should be invalid. 
            # Truly invalid links need to be handled separately,
            # likely by switching to using a path validator for
            # local URLs
            href = attrs['href']
            if href[0] == '#': return
            if not validators.url(href):
                href = urljoin(self.owner().homepage, href)
            self.handle_link(href)
        # return super().handle_starttag(tag, attrs)
    def handle_link(self, href):
        if self.owner().spawn(href):
            self.owner().graph.add_edge( (self.page, href) )
            # print((self.page, href))
    def handle_data(self, data):
        super().handle_data(data)

class Swarm:
    """swarmling factory"""
    def __init__(self, homepage):
        super().__init__()
        self.graph = SiteGraph()
        self.origin = homepage
        self.homepage = homepage
        self.pages = [homepage]  # first element is homepage
        self.run(homepage)
    def run(self, page):
        self._spawn(page)
        self.graph.compile_verts()
    def spawn(self, page):
        result = False
        if page not in self.pages and within_domain(page, self.homepage): 
            print('SPAWN>',page)
            self.pages.append(page)
            self._spawn(page)
        if within_domain(page, self.homepage):
            result = True
        return result
    def _spawn(self, page):
        try:
            byteread = urlopen(page)
            content = byteread.read().decode('utf-8')  # read and decode
            # print(content, '\n' + 50* '=' +'\n')
            ling = Swarmling(page, owner=self)
            ling.feed(content)
            ling.close()
        # TODO: Replace this excuse of error handling
        except HTTPError as e:
            print(e)

def main(args):
    if len(args) != 2:
        # IDEA: find a more specific exception/make one
        raise Exception('Too many arguments passed to the script')
    target = args[1]
    s = Swarm(target)

    # print('Pages: ')
    # [print(p) for p in s.pages]
    # print('Edges: ')
    # [print(e) for e in s.graph.edges]
    
    [print('{}\t:\t{}'.format(k,v)) for k,v in s.graph.sequential_verts().items()]

if __name__ == '__main__':
    main(sys.argv)
