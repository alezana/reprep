from . import (MIME_PNG, MIME_PYTHON, contract, ReportInterface,
               describe_value,
    describe_type, colorize_success, scale, posneg, Image_from_array, rgb_zoom,
    InvalidURL, NotExistent, MIME_SVG)
import sys
from StringIO import StringIO
from .utils.equality_mixin import CommonEqualityMixin
from . import logger

class Node(ReportInterface, CommonEqualityMixin):

    @contract(nid='valid_id|None', children='None|list', caption='None|str')
    def __init__(self, nid=None, children=None, caption=None):

        if children is not None and not isinstance(children, list):
            raise ValueError('Received a %s object as children list, should'
                             ' be None or list.' % describe_type(children))

        self.nid = nid

        if children is None:
            children = []

        self.childid2node = {}
        self.children = []
        for c in children:
            if not isinstance(c, Node):
                msg = 'Expected Node, got %s.' % describe_type(c)
                raise ValueError(msg)
            self.add_child(c)
        self.parent = None
        
        self.caption = caption

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        if len(self.children) != len(other.children):
            logger.error('children: %s vs %s' % (len(self.children),
                                                 len(other.children)))
            logger.error('his: %s' % other.children)
            logger.error('mine: %s' % self.children)
            return False 
        for i in range(len(self.children)):
            if self.children[i] != other.children[i]:
                logger.error('child %d' % i)
                logger.error('-mine: %s' % self.children[i])
                logger.error('- his: %s' % other.children[i])
                return False
            
        if self.caption != other.caption:
            logger.error('caption')
            return False 
        return True


    def add_child(self, n):
        ''' 
            Adds a child to this node. Usually you would not use this
            method directly. 
        '''
        assert n is not None
        if n.nid is not None:
            if n.nid in self.childid2node:
                raise Exception('Already have child with same id %r.' % n.nid)
        else:
            # give it a name
            n.nid = "%s%s" % (n.__class__.__name__, len(self.children))
            assert not n.nid in self.childid2node

        n.parent = self
        self.childid2node[n.nid] = n
        self.children.append(n)

    def has_child(self, nid):
        return nid in self.childid2node

    def last(self):
        ''' Returns the last added child Node. '''
        return self.children[-1]

    def node(self, nid, caption=None):
        ''' Creates a simple child node. '''
        from . import Node
        n = Node(nid, caption=caption)
        self.add_child(n)
        return n

    def resolve_url_dumb(self, url):
        assert isinstance(url, str)

        components = Node.url_split(url)
        if len(components) > 1:
            child = self.resolve_url_dumb(components[0])
            return child.resolve_url_dumb(Node.url_join(components[1:]))
        else:
            nid = components[0]
            if nid == '':
                raise InvalidURL(url)
            if nid == '..':
                if self.parent:
                    return self.parent
                else:
                    raise NotExistent('No parent.')

            l = dict([(child.nid, child) for child in self.children])
            if not nid in l:
                if self.nid == nid:
                    return self

                raise NotExistent('Could not find child %r; I know %s.' % 
                                  (nid, l.values()))
            return l[nid]

    @contract(url='str')
    def resolve_url(self, url, already_visited=None):
        if already_visited is None:
            already_visited = [self]
        else:
            if self in already_visited:
                raise NotExistent(url)
            already_visited += [self]

        if url.find('..') >= 0:
            # if it starts with .. we assume it's a precise url
            # and we don't do anything smart to find it
            return self.resolve_url_dumb(url)

        try:
            return self.resolve_url_dumb(url)
        except NotExistent:
            pass

        for child in self.children:
            try:
                return child.resolve_url(url, already_visited)
            except NotExistent:
                pass

        if self.parent:
            return self.parent.resolve_url(url, already_visited)
        else:
            # in the end, we get here
            raise NotExistent('Could not find url %r.' % url)

    def __getitem__(self, relative_url):
        return self.resolve_url(relative_url)

    @staticmethod
    def url_split(u):
        return u.split('/')

    @staticmethod
    def url_join(l):
        if not isinstance(l, list):
            raise ValueError('I expect a list, got "%s" (%s).' % (l, type(l)))
        return "/".join(l)

    def get_relative_url(self, other):
        assert isinstance(other, Node)
        if self == other:
            raise ValueError('I will not give you a relative url for myself.')
        all_my_parents = self.get_all_parents()

        if other in all_my_parents:
            levels = len(all_my_parents) - all_my_parents.index(other)
            url = Node.url_join(['..'] * levels)
            return url

        all_his_parents = other.get_all_parents()

        if self in all_his_parents:
            his_remaining = all_his_parents[all_his_parents.index(self) + 1:]
            components = [x.nid for x in his_remaining] + [other.nid]
            url = Node.url_join(components)
            return url

        common = [x for x in all_my_parents if x in all_his_parents]
        if not common:
            raise ValueError('The two nodes have no parents in common.')
        closest = common[-1]
        levels = len(all_my_parents) - all_my_parents.index(closest)
        his_remaining = all_his_parents[all_his_parents.index(closest) + 1:]
        components = (['..'] * levels + [x.nid for x in his_remaining]
                      + [other.nid])
        url = Node.url_join(components)

        try:
            assert self.resolve_url_dumb(url) == other
        except NotExistent:
            raise AssertionError('Produced url "%s" but does not work.' % url)

        return url

    def get_all_parents(self):
        ''' Returns a list of all parents. '''
        if self.parent:
            return self.parent.get_all_parents() + [self.parent]
        else:
            return []

    def print_tree(self, s=sys.stdout, prefix=""):
        s.write('%s- %s (%s)\n' % (prefix, self.nid, self.__class__))
        for child in self.children:
            child.print_tree(s, prefix + '  ')

    def format_tree(self):
        s = StringIO()
        self.print_tree(s)
        return s.getvalue()

    def get_complete_id(self, separator=":"):
        if not self.parent:
            return self.nid
        else:
            return self.parent.get_complete_id() + separator + self.nid

    def find_recursively(self, criterium):
        ''' 
            Finds the closest node in the family passing the criterium, 
            or None if none can be found. 
        '''
        if criterium(self):
            return self
        else:
            for child in self.children:
                res = child.find_recursively(criterium)
                if res is not None:
                    return res
            return None

    def get_first_available_name(self, prefix):
        for i in xrange(1, 1000):
            nid = '%s%d' % (prefix, i)
            if not self.has_child(nid):
                return nid
        assert False

