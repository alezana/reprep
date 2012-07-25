from . import (MIME_IMAGES, logger, Node, DataNode, contract, describe_type,
    MIME_WEB_IMAGES)
from .utils import indent
import warnings
from reprep.utils.equality_mixin import CommonEqualityMixin


class SubFigure(CommonEqualityMixin):
    def __init__(self, resource, image, web_image, caption):
        self.resource = resource
        self.image = image
        self.web_image = web_image
        self.caption = caption


class Figure(Node):

    @contract(cols='None|(int,>0)')
    def __init__(self, nid=None, caption=None, cols=None):
        Node.__init__(self, nid=nid)
        self.caption = caption
        self.cols = cols

        self.subfigures = []
        self.automatically_added = set()

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.caption != other.caption:
            return False
        if self.cols != other.cols:
            logger.error('Cols: %s %s' % (self.cols, other.cols))
            return False
        if self.subfigures != other.subfigures:
            logger.error('Sub: %s %s' % (self.subfigures, other.subfigures))
            return False
        return True

    def add_child(self, child):
        """ Automatically add child if it can be displayed. """
        Node.add_child(self, child)

        if (isinstance(child, DataNode) and
            child.get_first_child_with_mime(MIME_IMAGES)):
            self.sub(child, child.caption)
            self.automatically_added.add(child)

    def sub(self, resource, caption=None, display=None, **kwargs):
        ''' Adds a subfigure displaying the given resource. 
        
            resource can either be a string or a data node.
        '''

        if isinstance(resource, str):
            data = self.resolve_url(resource)
        elif isinstance(resource, Node):
            data = resource
        else:
            raise ValueError('The first parameter to sub() must be either'
                             ' a string (url) or a reference to a Node, '
                             ' not a %s.' % describe_type(resource))

        if caption is None:
            caption = data.caption
            if caption is None:
                caption = data.nid

        if data in self.automatically_added:
            warnings.warn('Node %r was automatically added to figure (new '
                          'behavior in 1.0).' % 
                          self.get_relative_url(data), stacklevel=2)
            return

        if not isinstance(data, DataNode):
            msg = ('I expect a DataNode as an argument to sub(), not a %s.'
                   % describe_type(resource))
            raise ValueError(msg)

        if display is not None:
            image = data.display(display, **kwargs)
        else:
            image = data.get_first_child_with_mime(MIME_IMAGES)

            if image is None:
                self.parent.print_tree() # XXX
                raise ValueError('Could not find candidate image for resource '
                                 '%r; image node is %r.' % 
                                 (resource, data.get_complete_id()))

        # Get an image that can be shown in a browser
        web_image = image.get_first_child_with_mime(MIME_WEB_IMAGES)
        if web_image is None:
            logger.error('No image with mime %r found in:\n%s' % 
                         (MIME_WEB_IMAGES, indent(image.format_tree(), '>')))
            # convert the image to web image
            # TODO: to write
            web_image = image # XXX
            logger.error('I need to convert %s into a web image.' % 
                         (image))

        sub = SubFigure(resource=self.get_relative_url(data),
                        image=self.get_relative_url(image),
                        web_image=self.get_relative_url(web_image),
                        caption=caption)
        self.subfigures.append(sub)

    def get_subfigures(self):
        return self.subfigures

