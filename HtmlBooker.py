import validators
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
from urllib.error import *
import sys
from html.parser import HTMLParser
from weakref import ref
import statistics as stats
from abc import ABCMeta
from html2text import html2text

# TODO: Rewrite this entire thing to work off a single table of contents if available
# talk about overengineering

visited_pages = {}

def within_domain(site, domain):
    """Determine whether the given site is in the
    given domain. This function is gross"""
    return (validators.url(site) and validators.url(domain) and 
            urlparse(site).netloc == urlparse(domain).netloc)

class PageVertex: 
    """simple object wrapper for SiteGraph object"""
    def __init__(self, obj, owngraph=None):
        self.obj = obj
        if owngraph is not None:
            self.owngraph = ref(owngraph)
        self.nbrs = []
    def addNbr(self, nbr):
        if nbr not in self.nbrs:
            self.nbrs.append(nbr) 
    def __eq__(self, other):
        return self.obj == other.obj
    def __str__(self):
        return 'VERT: ' + str(self.obj)
    def __repr__(self):
        return 'VERT: ' + repr(self.obj)
    def __hash__(self):
        return hash(self.obj)

# TODO: Rename page types as actual page types
# PageTypes
ABCMeta.__repr__ = lambda t: t.name

class Sequential(metaclass=ABCMeta):
    name = 'Sequential'
class SequenceCap(metaclass=ABCMeta):
    name = 'SequenceCap'
SequenceCap.register(Sequential)
class NonSequential(metaclass=ABCMeta):
    name = 'NonSequential'
class SiteMap(metaclass=ABCMeta):
    name = 'SiteMap'

class SiteGraph:
    """a directed graph of a domain's hyper links, ignoring
    external links"""
    def __init__(self):
        self.vertices = []  # rename to verts
        self.edges = []
    def add_edge(self, edge):
        """add a 2-tuple of vertices that exist in the graph"""
        assert len(edge) == 2
        edge = (PageVertex(edge[0], self), PageVertex(edge[1],self))
        for e in edge:
            if e not in self.vertices:
                self.add_vertex(e)
        if edge not in self.edges:
            self.edges.append(edge)
    def add_vertex(self, vert):
        """wrap any object as a vertex"""
        if type(vert) != PageVertex:
            vert = PageVertex(vertex, self)
        self.vertices.append(vert)
    def compile_verts(self):
        """compiles vertex info"""
        for v in self.vertices:
            for e in (e for e in self.edges if e[0] == v ):
                v.addNbr(e[1])
    def get_vert(self, page):
        for v in self.vertices:
            if v.obj == page:
                return v
    def get_page_types(self):
        """determine the page types of all verts"""
        linksto = {}
        for v in self.vertices:
            other_verts = self.vertices.copy()
            other_verts.remove(v)
            linksto[v] = sum( (v in u.nbrs for u in other_verts) )
        linksfrom = {}
        for v in self.vertices:
            linksfrom[v] = len(v.nbrs)
        # use statistical mode to determine whether pages are sequential and how
        mode = stats.mode(linksto.values())
        result = {}
        for v in linksto:
            if linksto[v] == mode:
                result[v] = Sequential
            elif linksto[v] == mode-1:
                result[v] = SequenceCap
            else:
                result[v] = NonSequential
        # find the nonsequential page with the most links
        nonseqpages = [k for k in linksfrom if result[k] == NonSequential]
        # print(nonseqpages)
        # print('Linksfrom:', linksfrom)
        sitemappage = max(nonseqpages, key=lambda t: linksfrom[t])
        result[sitemappage] = SiteMap
        # dirty fix TODO integrate this fix into the process itself
        result = {k.obj:v for k,v in result.items()}
        return result
            
class Swarmling(HTMLParser):
    """html page processor from the swarm"""
    def __init__(self, page, owner=None):
        assert owner is not None
        self.owner = ref(owner)
        self.page = page
        self.reset()
        super().__init__()
    def feed(self, content):
        global visited_pages
        visited_pages[self.page] = content
        return super().feed(content)
    def handle_starttag(self, tag, attrs):
        # convert attrs to dict to support attribute mapping;
        # for links this should be fine, but some attributes
        # might have multiple values
        # TODO: use some kind of multidict for attrs
        # TODO: ignore URLs like "mailto:"
        attrs = {k:v for k,v in attrs}
        if tag == 'a' and 'href' in attrs:
            # if the URL is local, it should be invalid. 
            # Truly invalid links need to be handled separately,
            # likely by switching to using a path validator for
            # validaing local URLs
            href = attrs['href']
            if href[0] == '#': return
            if not validators.url(href):
                href = urljoin(self.owner().homepage, href)
            self.handle_link(href)
    def handle_link(self, href):
        if self.owner().spawn(href):
            self.owner().graph.add_edge( (self.page, href) )
    def handle_data(self, data):
        return super().handle_data(data)

class Swarm:
    """factory that employs swarmlings to
    gather data on its target site's link layout"""
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
        """safe spawner, returns the condition of whetheri
        it actually decided to spawn on the target location"""
        result = False
        if page not in self.pages and within_domain(page, self.homepage): 
            # print('SPAWN>',page)
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

class TOCParser(HTMLParser):
    """table of contents parser"""
    def __init__(self, homepage):
        self.homepage = homepage
        self.reset()
        self.links = []
        super().__init__()
    def handle_starttag(self, tag, attrs):
        attrs = {k:v for k,v in attrs}
        if tag == 'a' and 'href' in attrs:
            href = attrs['href']
            if href[0] == '#': return
            if not validators.url(href):
                href = urljoin(self.homepage, href)
            if within_domain(href, self.homepage):
                self.links.append(href)
    def get_toc_order(self):
        return self.links

def order_pages(swarm):
    pages = swarm.graph.get_page_types()
    # find table of contents
    tableofcon = ''
    for p in pages:
        if pages[p] == SiteMap:
            tableofcon = p
    assert tableofcon
    tableproc = TOCParser(swarm.homepage)
    tableproc.feed(visited_pages[swarm.homepage])
    tableproc.close()
    order = tableproc.get_toc_order()
    order = [p for p in order if pages[p] == SequenceCap]
    start = swarm.graph.get_vert(order[0])
    end = swarm.graph.get_vert(order[1])
    # follow the links from the start to the end
    result = []
    prv = swarm.graph.get_vert(swarm.homepage)
    curr = start
    while curr != end:
        result.append(curr.obj)
        nxt = []
        for nbr in curr.nbrs:
            if (pages[nbr.obj] in (Sequential, SequenceCap)
                and nbr != prv 
                and nbr != curr):
                # hacky, something is wrong here
                nbr = swarm.graph.get_vert(nbr.obj)
                nxt.append(nbr)
        prv = curr
        curr = nxt[0]
    result.append(end.obj)
    return result

# TODO: move a lot of pieces i.e. main swarm and target into the global scope
# TODO: separate pieces into multiple files
# NOTE: create a case-by-base analysis for different html books,
# those with table of contents (get book order right there), those without, etc
def main(args):
    if len(args) != 2:
        # TODO: find a more specific exception/make one
        raise Exception('Too many arguments passed to the script')
    target = args[1]
    # The swarm will take its time determining all the pages on
    # the target, and their types relative to reformating it 
    # into a book
    s = Swarm(target)
    # [print(i, '\n\t', i.nbrs) for i in s.graph.vertices]
    book = order_pages(s)
    with open('out', 'r+') as f:
        for p in book:
            # print(p)
            f.write(html2text(visited_pages[p]))

if __name__ == '__main__':
    main(sys.argv)
