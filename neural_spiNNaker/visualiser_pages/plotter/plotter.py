__author__ = 'stokesa6'

import gtk
import cairo


#helper class to get the visuliaser to generate a plot inside the gui
class Plot (gtk.DrawingArea):
    """
    Abstract class representing a gtk.DrawingArea holding a plot.
    """

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("size-allocate", self.size_allocate)

        self._surface = None
        self._options = None

    def set_options(self, options):
        """Set plot's options"""
        self._options = options

    def set_data(self, data):
        pass

    def plot(self):

        pass

    def expose(self, widget, event):
        context = widget.window.cairo_create()
        context.rectangle(event.area.x, event.area.y, event.area.width,
                          event.area.height)
        context.clip()
        self.draw(context)

        return False

    def draw(self, context):
        rect = self.get_allocation()
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                           rect.width, rect.height)

        self.plot()
        context.set_source_surface(self._surface, 0, 0)
        context.paint()

    def size_allocate(self):
        self.queue_draw()