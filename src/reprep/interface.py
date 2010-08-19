import mimetypes

class NodeInterface: 
 
    def data(self, id, data, mime=None, desc=None):
        ''' Attaches a data child to this note. 
        
            "data" is assumed to be a raw python structure. 
            Or, if data is a string representing a file, 
            pass a proper mime type (mime='image/png'). '''
        if not isinstance(id, str):
            raise ValueError('The ID must be a string, not a %s' % \
                             id.__class__.__name__) 
        from reprep import DataNode
        n = DataNode(id=id, data=data, mime=mime)
        self.add_child(n) 
        return n
    
    def data_file(self, id, mime):
        ''' Support for attaching data from a file. 
        This method is supposed to be used in conjunction with the "with"
        construct. 
        
        For example, the following is the concise way to attach a pdf
        plot to a node.::
        
            with report.data_file('my_plot', 'application/pdf') as f:
                pylab.figure()
                pylab.plot(x,y)
                pylab.title('my x-y plot')
                pylab.savefig(f)
        
        Omit any file extension from 'id', ("my_plot" and not "my_plot.pdf"), 
        we will take care of it for you.
        
        This is a more complicated example, where we attach two versions
        of the same image, in different formats::
         
            for format in ['application/pdf', 'image/png']:
                with report.data_file('plot', format) as f:
                    pylab.figure()
                    pylab.plot(x,y)
                    pylab.savefig(f)

        '''
        from helpers import Attacher
        
        if not mimetypes.guess_extension(mime):
            raise Exception('Cannot guess extension for MIME "%s".' % mime)
        
        return Attacher(self, id, mime)
 
    def figure(self, id, *args, **kwargs):
        ''' Attaches a figure to this node. '''
        from reprep import Figure
        f = Figure(id, *args, **kwargs)
        self.add_child(f) 
        return f
 
    def table(self, id, data, col_desc=None, row_desc=None):
        ''' Attaches a table to this node. '''
        from reprep import Table
        t = Table(id, data, col_desc, row_desc)
        self.add_child(t) 
        return t
        
