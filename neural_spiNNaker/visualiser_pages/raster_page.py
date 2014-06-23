from __builtin__ import sorted
__author__ = 'stokesa6'
import gtk
from neural_spiNNaker.visualiser_pages.plotter.scatter_plotter import ScatterplotChart
from visualiser.abstract_page import AbstractPage
import math
import logging
logger = logging.getLogger(__name__)


class RasterPage(AbstractPage):
    def __init__(self, vertex_in_question, raster_x_scope,
                 do_fading, runtime, machine_time_step,
                 current_vertex=None, merged=True):
        AbstractPage.__init__(self)
        self.is_merged_version = merged
        self.last_timer_tic = None
        #holds all the vertexes being recorded for spikes
        if vertex_in_question is None:
            self.vertex_in_question = list()
            self.vertex_in_question.append(current_vertex)
        else:
            self.vertex_in_question = sorted(vertex_in_question,
                                             key=lambda vertex: vertex.label)

        #creates a collection of offsets for y plot
        self.off_sets = list()
        self.machine_time_step = machine_time_step

        current_off_set = 0

        self.x_axis_scope = raster_x_scope
        if self.x_axis_scope == "None":
            self.x_axis_scope = runtime
        if self.x_axis_scope is None:
            self.x_axis_scope = 2000.0
        
        self.do_fading = do_fading
        self.data_stores = []
            
        for current_vertex in self.vertex_in_question:
            label = str(current_vertex.label)
            self.data_stores.append(label)
            tuple_data = [(-1, -1), (-1, -1)]
            self.data_stores.append(tuple_data)
            self.off_sets.append(current_off_set)
            current_off_set += current_vertex.atoms + 15

        #records the maxiumum neuron value
        self.max_y_value = current_off_set

        #set name of page
        self.page = gtk.Frame("raster plot")

        self.figure = None
        self.plot = ScatterplotChart()
        self.axis = None
        self.canvas = None
        self.graphview = None
        #generate plot
        self.generate_plot(0, True)

    def add_vertex(self, vertex_to_add):
        label = vertex_to_add.label
        if label is None:
            label = "Unknown"
        self.data_stores.append(label)
        tuple_data = [(-1, -1), (-1, -1)]
        self.data_stores.append(tuple_data)
        self.off_sets.append(self.max_y_value)

        #records the maxiumum neuron value
        self.max_y_value += vertex_to_add.atoms + 15
        self.redraw(self.last_timer_tic)

    def remove_vertex(self, vertex_to_remove):
        index = self.data_stores.index(vertex_to_remove.label)
        self.data_stores.pop(index)
        self.data_stores.pop(index)
        value = self.off_sets.pop(index)
        for elements in range(index, len(self.off_sets)):
            self.off_sets[index] -= value
        self.max_y_value -= (vertex_to_remove.atoms + 15)
        if len(self.data_stores) == 0:
            self.main_pages.remove(self.page)

    def generate_plot(self, current_time_tics, initial):
        current_time = ((current_time_tics * self.machineTimeStep) / 1000.0)
        if current_time > float(self.x_axis_scope):
            xaxix = current_time - int(self.x_axis_scope)
        else:
            xaxix = 0
        current_top_x = xaxix + int(self.x_axis_scope)
        range_x = int(self.x_axis_scope)
        gap = math.floor(range_x / 10)

        xticks = [dict(v=math.floor((position * gap) + xaxix),
                       label=math.floor((position * gap) + xaxix))
                  for position in range(10)]

        yticks = dict()
        colours = list()
        i = 0
        for vertex in self.vertex_in_question:
            index = self.vertex_in_question.index(vertex)
            offset = self.off_sets[index]
            yticks[offset] = "%s - %d" % (vertex.label, 0)
            counter = offset + vertex.atoms
            yticks[counter] = "%d" % vertex.atoms
            if i % 2 == 0:
                colours.append("#ff0000")
            else:
                colours.append("#0000ff")
            i += 1

        y_axis_ticks = [dict(v=key, label=yticks[key]) for key in yticks.keys()]

        options = {'axis':
                   {'x':
                    {'ticks': xticks,
                     'label': 'time(ms)',
                     'range': [xaxix, current_top_x]},
                    'y':
                    {'tickCount': 4,
                     'ticks': y_axis_ticks,
                     'rotate': 0,
                     'label': 'NeuronID',
                     'range': [0, self.max_y_value]},
                    'labelFontSize': 16,
                    'tickFontSize': 14, },
                   'legend':
                   {'hide': False,
                    'position': 
                    {'top': 20, 
                     'right': 0, 
                     'bottom': None, 
                     'left': None}, },
                   'background':
                   {'chartColor': '#ffffff', },
                   'padding': {'right': 50},
                   'colorScheme': 
                   {'name': 
                    'fixed',
                    'args': 
                    {'colors': colours}}}

        self.plot.set_options(options)
        if initial:
            for index in range(len(self.vertex_in_question)):
                true_index = (index * 2)
                self.plot.set_data(self.data_stores[true_index],
                                   self.data_stores[true_index+1])
            self.page.add(self.plot)
            self.page.show_all()
        self.page.queue_draw()

    def redraw(self, timer_tic):
        self.last_timer_tic = timer_tic
        if timer_tic <= ((self.run_time * 1000.0) / 
                         self.machineTimeStep):
            self.generate_plot(timer_tic, False)
            self.page.queue_draw()

    def recieved_spike(self, details):
        """
        translates the spike into a x and y axis and updates the data_store
        """
        for vert in self.vertex_in_question:
            for subvert in vert.subvertices:
                chip = subvert.placement.processor.chip
                processor = subvert.placement.processor
                if chip.get_coords()[0] == details['coords'][0] and \
                   chip.get_coords()[1] == details['coords'][1] and \
                   processor.idx == details['coords'][2] + 1:
                    logger.debug("Spike from %d, %d, %d, %d is from population"
                                 " %s" % (details['coords'][0], 
                                          details['coords'][1], 
                                          details['coords'][2] + 1, 
                                          details['neuron_id'], vert.label))
                    self.update_data_store_with_spike(subvert, 
                                                      details['neuron_id'],
                                                      details['time_in_ticks'])
        if self.do_fading:
            self.remove_stale_values(details['time_in_ticks'])

    def update_data_store_with_spike(self, subvertex, local_neuron_id,
                                     time_in_tics):
        """
        modifies the data given and places data into data_store
        """
        #calcualte correct y axis
        index = self.vertex_in_question.index(subvertex.vertex)
        offset = self.off_sets[index]
        pop_neuron_id = subvertex.lo_atom + local_neuron_id
        offsetted_neuron_id = pop_neuron_id + offset
        #calculate correct x axis
        xaxix = (time_in_tics * self.dao.machineTimeStep) / 1000  # to ms
        true_index = (index * 2) + 1
        self.data_stores[true_index].append((xaxix, offsetted_neuron_id))

    def remove_stale_values(self, time_in_tics):
        """
        remove all data points that are over the theshold ago
        """
        xaxix = (time_in_tics * self.dao.machineTimeStep) / 1000  # to ms
        for data_store_index in range(1, len(self.data_stores), 2):
            data = self.data_stores[data_store_index]
            for data_piece in data:
                if (xaxix - data_piece[0]) > int(self.x_axis_scope):
                    data.remove(data_piece)