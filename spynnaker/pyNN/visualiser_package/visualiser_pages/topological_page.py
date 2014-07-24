from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.visualiser_package.visualiser_pages.\
    abstract_live_spike_page import AbstractLiveSpikePage
import math
import gtk
import cairo
import logging
logger = logging.getLogger(__name__)


class TopologicalPage(AbstractLiveSpikePage):
    def __init__(self, vertex_in_question, retina_drop_off_theshold,
                 subgraph, placements, transciever, has_board):
        AbstractLiveSpikePage.__init__(self, transciever, has_board)

        self._rectangle_size = {'x': 1, 'y': 1}
        self._exposure_bar_size = 20
        self._exposure_bar_label_size = 40
        self._exposure_bar_space_size = 20
        self._legend_size = {'x': 40, 'y': 20}
        self._no_blocks_in_exposure_plot = 200
        self._no_labels = 10
        self._no_color_mapping_labels = 10
        self._pixmap = None

        #holds all the vertexes being recorded for spikes
        self._vertex_in_question = vertex_in_question

        if self._vertex_in_question.visualiser_reset_counters:
            self._data = dict()
            self._data['t'] = \
                self._vertex_in_question.visualiser_reset_counter_period
            self._data['p'] = self
            self._data['pt'] = None
        else:
            self._data = None

        self._placement_fudge = None
        if getattr(self._vertex_in_question,
                   "get_packet_retina_coords", None) is None:
            
            self._no_block_in_exposure_plot = \
                vertex_in_question.visualiser_no_colours
            self._no_color_mapping_labels = \
                vertex_in_question.visualiser_no_colours

        self._drawing_area = None
        self._objects_to_draw = dict()
        self.lo_atom_mapping = dict()
        for subvert in subgraph.get_subvertices_from_vertex(vertex_in_question):
            placement = placements.get_placement_of_subvertex(subvert)
            key = "{}:{}:{}".format(placement.x, placement.y, placement.p)
            self.lo_atom_mapping[key] = subvert.lo_atom
        self._max_color_value = {'r': 1, 'g': 1, 'b': 1}
        self._min_color_value = {'r': 0, 'g': 0, 'b': 0}
        number_of_neurons = (self._vertex_in_question.subvertices[0].hi_atom -
                             self._vertex_in_question.subvertices[0].lo_atom)
        if (vertex_in_question.visualiser_2d_dimensions['x'] is None or
           vertex_in_question.visualiser_2d_dimensions['y'] is None):
                self._x_dim = int(math.sqrt(number_of_neurons))
                self._y_dim = int(math.sqrt(number_of_neurons))
                vertex_in_question.visualiser_2d_dimensions = {'x': self._x_dim,
                                                               'y': self._y_dim}
        else:
            self._x_dim = vertex_in_question.visualiser_2d_dimensions['x']
            self._y_dim = vertex_in_question.visualiser_2d_dimensions['y']

        #values for tracking color increases
        self._initial_value = 0
        self._max_seen_value = 50
        self._min_seen_value = 0
        self._needs_reseting = False
        self._spikes_that_need_processing = list()
        self._drawing = False

        #holders for determining if you need to redraw
        # everything, or just a section
        self._new_entries = list()
        self._redraw_everything = True

        self._exposure_bar_mapping = dict()

        #stores a offset needed for fading
        self._retina_drop_off_theshold = retina_drop_off_theshold
        self._data_stores = []

       # print self.vertex_in_question
        self._label = self._vertex_in_question.label
        if self._label is None:
            self._label = "Unknown"

        #set name of page
        self._page = gtk.Frame("topological plot")
        
        #generate plot area
        self._generate_plot()

        #generate objects to draw
        self._generate_objects()

        #generate the rectangles that represent the retina view
        self._generate_retina_view()

    def _generate_objects(self):
        """
        generates the drawable objects in an array
        """
        max_y_pos = \
            (self._y_dim * self._rectangle_size['y']) - self._legend_size['x']
        
        for x in range(self._x_dim):
            for y in range(self._y_dim):
                x_pos = (x * self._rectangle_size['x']) + self._legend_size['x']
                y_pos = y * self._rectangle_size['y']
                width = self._rectangle_size['x']
                height = self._rectangle_size['y']
                colour = self._initial_value
                y_pos = max_y_pos - self._legend_size['y'] - y_pos
                key = "{}:{}".format(int(x), int(y))
                self._objects_to_draw[key] = {'x': int(x_pos),
                                              'y': int(y_pos),
                                              'w': int(width),
                                              'h': int(height),
                                              'c': colour}

    def _generate_retina_view(self):
        """
        generates the rectangles that represent the retina view and sets them to
        the colour black initially.

        NOTE the size is govenered by the neurons in the external device. (has
        to be a size shaped)
        """
        height_of_screen = self._y_dim * self._rectangle_size['y']
        width_of_screen = self._x_dim * self._rectangle_size['x']
        ##add exposureBar
        width = width_of_screen + (self._exposure_bar_size +
                                   self._exposure_bar_label_size +
                                   self._exposure_bar_space_size)
        height = height_of_screen
        #add legends to screen
        width += self._legend_size['x']
        height += self._legend_size['y']

        #sets up the drawing area size
        self._drawing_area.set_size_request(int(width), int(height))

    def _generate_plot(self):
        """
        generates the initial drawing area and ties it into the page
        """
        self._drawing_area = gtk.DrawingArea()
        self._drawing_area.connect("expose_event", self.expose)
        self._drawing_area.connect("size-allocate", self._size_allocate)
        self._page.add(self._drawing_area)
        self._page.show_all()

    def expose(self, widget):
        """
        when the drawing area is exposed, redraw the rectangle
        """
        #get drawing area writable object
        #print "started the expose"
        cr = widget.window.cairo_create()

        #check that entries havent fallen off the theshold
        if self._needs_reseting:
            #print "starting resetting"
            self._adjust_values_to_fit_in_range()

        #add the exposure bar
        self._add_exposure_bar(cr)

        #do legend
        self._add_exposure_legend(cr)

       # print "seen min is now {}".format(self.min_seen_value)

        #if self.redraw_everything:
        for drawable_object_key in self._objects_to_draw.keys():
            self._draw_object(cr, self._objects_to_draw[drawable_object_key])
        #else:
         #   for new_entry_key in self.new_entries:
          #      drawable_object = self.objects_to_draw[new_entry_key]
           #     self.draw_object(cr, drawable_object)
           # self.new_entries = list()

        #add axises
        self._add_x_y_axis_labels(cr)
       # print "finished the expose"
        self._drawing = False

    def _adjust_values_to_fit_in_range(self):
        """
        this method resets the color keys of the color mapper
        so that stuff can be adjusted to reflect changes in values
        """
        #print "doing reset"
        self._needs_reseting = False
        self._redraw_everything = True
       # print "min value is {}".format(self.min_seen_value)
        if 0 != self._min_seen_value:
            diff = 0 - self._min_seen_value
            #print "diff is {}".format(diff)
            for drawable_key in self._objects_to_draw.keys():
                old_object = self._objects_to_draw[drawable_key]
                old_value = old_object['c']
                new_value = old_value + diff
                if new_value > self._max_seen_value:
                    self._set_max_seen_value(new_value)
                self._objects_to_draw[drawable_key] = {'x': old_object['x'],
                                                       'y': old_object['y'],
                                                       'w': old_object['w'],
                                                       'h': old_object['h'],
                                                       'c': new_value}
        if self._max_seen_value > 765:
            ratio = self._max_seen_value / 766.0
            #print "ratio is {} and max is {}".format(ratio,
            #                                         self.max_seen_value)
            self._max_seen_value = 0
            for drawable_key in self._objects_to_draw.keys():
                old_object = self._objects_to_draw[drawable_key]
                old_value = old_object['c']
                new_value = old_value / ratio
               # print "new value is {}".format(int(math.floor(new_value)))
                if new_value > self._max_seen_value:
                    self._set_max_seen_value(int(math.floor(new_value)))
                self._objects_to_draw[drawable_key] = {'x': old_object['x'],
                                                       'y': old_object['y'],
                                                       'w': old_object['w'],
                                                       'h': old_object['h'],
                                                       'c': int(new_value)}
      #  print "seen min is {}".format(self.min_seen_value)
        self._min_seen_value = 0
       # print "seen min is {}".format(self.min_seen_value)

    def _draw_object(self, cr, drawable_object):
        """
        draws an object onto the drawable writable object
        """
        #set the color for the object
        value = drawable_object['c']
        color_to_draw = self._exposure_bar_mapping[value]

        cr.set_source_rgb(color_to_draw['r'],
                          color_to_draw['g'],
                          color_to_draw['b'])
        #create a rectangle for the object
        cr.rectangle(drawable_object['x'], drawable_object['y'],
                     drawable_object['w'], drawable_object['h'])
        cr.fill()

    def _add_x_y_axis_labels(self, cr):
        height_of_screen = self._y_dim * self._rectangle_size['y']
        y_position = math.floor(self._y_dim / self._no_labels)
        x_position = math.floor(self._x_dim / self._no_labels)
        #set axis font and color
        cr.set_source_rgb(0, 0, 0)  # black
        cr.select_font_face("Purisa",
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)

        #do x axis
        for x_position_2 in range(self._no_labels):
            x_loc = (x_position * x_position_2)
            object_key = "{}:{}".format(int(x_loc), 0)
            x_screen_pos = self._objects_to_draw[object_key]['x']
            y_screen_pos = height_of_screen + self._rectangle_size['y']
            cr.move_to(x_screen_pos, y_screen_pos)
            cr.show_text("{}".format(x_loc))

        #do y axis
        for y_position_2 in range(self._no_labels):
            y_loc = (y_position * y_position_2)
            object_key = "{}:{}".format(0, int(y_loc))
            y_screen_pos = self._objects_to_draw[object_key]['y']
            cr.move_to(0, y_screen_pos)
            cr.show_text("{}".format(y_loc))

    def _add_exposure_bar(self, cr):
        """
        adds the exposure bar to the side of the window
        """
        height_of_screen = self._y_dim * self._rectangle_size['y']
        width_of_screen = self._x_dim * self._rectangle_size['x']
        position_of_bar = width_of_screen + (self._exposure_bar_size +
                                             self._exposure_bar_label_size +
                                             self._exposure_bar_space_size)
        #set color of cr to black
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(position_of_bar, 0, self._exposure_bar_size,
                     height_of_screen)
        cr.fill()
        colors_to_use = 767
        #go though the bar adding a rectangle for each clolor shift
        #769
        self._placement_fudge = \
            math.floor(colors_to_use / self._no_blocks_in_exposure_plot)
        for value in range(767):
            orignal_value = value
            if value > 255:
                r = 1
                value -= 255
            else:
                r = ((1.0 / 255.0) * value)
                value = 0

            if value > 255:
                g = 1
                value -= 255
            else:
                g = ((1.0 / 255.0) * value)
                value = 0

            b = (1.0 / 255.0 * value)
            self._exposure_bar_mapping[orignal_value] = {'r': r, 'g': g, 'b': b}
            if orignal_value % self._placement_fudge == 0:
                cr.set_source_rgb(r, g, b)
                y = (height_of_screen -
                     ((height_of_screen / self._no_blocks_in_exposure_plot)
                      * (orignal_value / self._placement_fudge)))
                cr.rectangle(position_of_bar, y, self._exposure_bar_size,
                             height_of_screen / self._no_blocks_in_exposure_plot)
                cr.fill()

    def _add_exposure_legend(self, cr):
        #ADD LEGEND
        height_of_screen = self._y_dim * self._rectangle_size['y']
        width_of_screen = self._x_dim * self._rectangle_size['x']
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Purisa",
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)
        #put 10 labels to the colour mapping
        range_of_color_values = self._max_seen_value - self._min_seen_value
        per_setp = math.floor(range_of_color_values /
                              self._no_color_mapping_labels)
        for index in range(self._no_color_mapping_labels + 1):
            position = (per_setp * index) / self._placement_fudge
            y = (height_of_screen -
                (height_of_screen / self._no_color_mapping_labels) * index)
            x = (width_of_screen + self._exposure_bar_size +
                 (self._exposure_bar_label_size / 2))
            cr.move_to(x, y)
            cr.show_text("{}".format(position))

    def _size_allocate(self, requisition):
        """'
        when the size is allocated, redraw the drawing area
        """
        #determine new size of a rectangle
        self._redraw_everything = True
        if len(self._objects_to_draw.keys()) != 0:
            width = requisition.width
            height = requisition.height
            x = (width - self._exposure_bar_size - self._exposure_bar_label_size -
                 self._exposure_bar_space_size - self._legend_size['x'])
            x = math.floor(x / self._x_dim)
            y = math.floor((height - self._legend_size['y']) / self._y_dim)
            self._rectangle_size = {'x': x, 'y': y}
            #go through drawing objects updating new x,y width and height
            max_y_pos = self._y_dim * self._rectangle_size['y']
            for x in range(self._x_dim):
                for y in range(self._y_dim):
                    x_pos = ((x * self._rectangle_size['x']) +
                             self._legend_size['x'])
                    y_pos = y * self._rectangle_size['y']
                    width = self._rectangle_size['x']
                    height = self._rectangle_size['y']
                    object_key = "{}:{}".format(x, y)
                    colour = self._objects_to_draw[object_key]['c']
                    y_pos = max_y_pos - self._legend_size['y'] - y_pos
                    object_key = "{}:{}".format(int(x), int(y))
                    self._objects_to_draw[object_key] = {'x': int(x_pos),
                                                         'y': int(y_pos),
                                                         'w': int(width),
                                                         'h': int(height),
                                                         'c': colour}
            self._drawing_area.queue_draw()

    # noinspection PyUnusedLocal
    def redraw(self, timer_tic):
        """
        method used by the main visualiser to promt this page to be redrawn
        :param timer_tic:
        """
        if not self._drawing:
            self._drawing = True
            blocked_list = self._spikes_that_need_processing
            self._spikes_that_need_processing = list()
            for details in blocked_list:
                self._redraw_everything = False
                if getattr(self._vertex_in_question, "get_packet_retina_coords",
                           None) is not None:
                    x, y, spike_value = \
                        self._vertex_in_question.\
                        get_packet_retina_coords(details['spike_word'],
                                                 self._y_dim)
                else:
                    ##assuming its a normal pop with a topolgoical view,
                    # use x then y
                    x, y, spike_value = \
                        self._convert_pop_spike_to_x_y(details['spike_word'])
                #translate spike value into a increase or decrease in color
                if spike_value != 1:
                    spike_value = -1

                #update the object
                object_key = "{}:{}".format(int(x), int(y))
                old_object = self._objects_to_draw[object_key]
                new_color = old_object['c'] + (spike_value *
                                               self._placement_fudge)
                #store it into min and maxes if needed
                if new_color < self._min_seen_value:
                    self._set_min_seen_value(new_color)
                if new_color > self._max_seen_value:
                    self._set_max_seen_value(new_color)

                new_object = {'x': old_object['x'],
                              'y': old_object['y'],
                              'w': old_object['w'],
                              'h': old_object['h'],
                              'c': new_color}
                #replace obect in drawable objects
                self._objects_to_draw[object_key] = new_object
                #track that this obejct needs redrawing
                self._new_entries.append(object_key)
            self._drawing_area.queue_draw()

    def recieved_spike(self, details):
        """
        takes a spike detials and converts it into a update in the retina screen
        """
        self._spikes_that_need_processing.append(details)

    def _set_min_seen_value(self, new_value):
        """
        this tracks the new min value until the next resetting of the color map
        """
        if not self._needs_reseting:
            self._needs_reseting = True
        self._min_seen_value = new_value

    def _set_max_seen_value(self, new_value):
        """
        this tracks the new max value until the next resetting of the color map
        """
       # print "setting max to {}".format(new_value)
        if not self._needs_reseting:
            self._needs_reseting = True
        self._max_seen_value = new_value

    def _convert_pop_spike_to_x_y(self, spike_word):
        """
        takes the spike_word (key) and converts it into a neuron id, for the
        vertex it then converts the neuron id into a x and y coord and adds
        one to the colour
        """
        neuron_id = packet_conversions.get_nid_from_key(spike_word)
        x = packet_conversions.get_x_from_key(spike_word)
        y = packet_conversions.get_y_from_key(spike_word)
        p = packet_conversions.get_p_from_key(spike_word)
        lo_atom = self.lo_atom_mapping["{}:{}:{}".format(x, y, p)]
        real_neuron_id = lo_atom + neuron_id
        x_coord = math.floor(real_neuron_id / self._y_dim)
        y_coord = real_neuron_id - (x_coord * self._y_dim)
        return x_coord, y_coord, 1

    def _reset_values(self):
        for old_object_key in self._objects_to_draw.keys():
            old_object = self._objects_to_draw[old_object_key]
            new_object = {'x': old_object['x'],
                          'y': old_object['y'],
                          'w': old_object['w'],
                          'h': old_object['h'],
                          'c': 0}
            #replace obect in drawable objects
            self._objects_to_draw[old_object_key] = new_object

    def _get_reset(self):
        if self._data is not None:
            return self._data
        else:
            return None

    def set_reset(self, data):
        self._data = data