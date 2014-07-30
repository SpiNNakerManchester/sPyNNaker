from __builtin__ import sorted
import gtk
from spynnaker.pyNN.visualiser_package.visualiser_pages.plotter.\
    scatter_plotter import ScatterplotChart
from spynnaker.pyNN.visualiser_package.visualiser_pages.\
    abstract_live_spike_page import AbstractLiveSpikePage
import math
import logging
logger = logging.getLogger(__name__)


class RasterPage(AbstractLiveSpikePage):
    def __init__(self, vertex_in_question, raster_x_scope, do_fading, runtime,
                 machine_time_step, transciever, has_board, current_vertex=None,
                 merged=True):
        AbstractLiveSpikePage.__init__(self, transciever, has_board)
        self._is_merged_version = merged
        self._last_timer_tic = None
        #holds all the vertexes being recorded for spikes
        if vertex_in_question is None:
            self._vertex_in_question = list()
            self._vertex_in_question.append(current_vertex)
        else:
            self._vertex_in_question = sorted(vertex_in_question,
                                              key=lambda vertex: vertex.label)

        #creates a collection of offsets for y plot
        self._off_sets = list()
        self._machine_time_step = machine_time_step
        self._runtime = runtime

        current_off_set = 0

        self._x_axis_scope = raster_x_scope
        if self._x_axis_scope == "None":
            self._x_axis_scope = runtime
        if self._x_axis_scope is None:
            self._x_axis_scope = 2000.0
        
        self._do_fading = do_fading
        self._data_stores = []
            
        for current_vertex in self._vertex_in_question:
            label = str(current_vertex.label)
            self._data_stores.append(label)
            tuple_data = [(-1, -1), (-1, -1)]
            self._data_stores.append(tuple_data)
            self._off_sets.append(current_off_set)
            current_off_set += current_vertex.n_atoms + 15

        #records the maxiumum neuron value
        self._max_y_value = current_off_set

        #set name of page
        self._page = gtk.Frame("raster plot")

        self._figure = None
        self._plot = ScatterplotChart()
        self._axis = None
        self._canvas = None
        self._graphview = None
        #generate plot
        self._generate_plot(0, True)

    def add_vertex(self, vertex_to_add):
        label = vertex_to_add.label
        if label is None:
            label = "Unknown"
        self._data_stores.append(label)
        tuple_data = [(-1, -1), (-1, -1)]
        self._data_stores.append(tuple_data)
        self._off_sets.append(self._max_y_value)

        #records the maxiumum neuron value
        self._max_y_value += vertex_to_add.n_atoms + 15
        self.redraw(self._last_timer_tic)

    def remove_vertex(self, vertex_to_remove):
        index = self._data_stores.index(vertex_to_remove.label)
        self._data_stores.pop(index)
        self._data_stores.pop(index)
        value = self._off_sets.pop(index)
        for elements in range(index, len(self._off_sets)):
            self._off_sets[index] -= value
        self._max_y_value -= (vertex_to_remove.n_atoms + 15)

    def _generate_plot(self, current_time_tics, initial):
        current_time = ((current_time_tics * self._machine_time_step) / 1000.0)
        if current_time > float(self._x_axis_scope):
            xaxix = current_time - int(self._x_axis_scope)
        else:
            xaxix = 0
        current_top_x = xaxix + int(self._x_axis_scope)
        range_x = int(self._x_axis_scope)
        gap = math.floor(range_x / 10)

        xticks = [dict(v=math.floor((position * gap) + xaxix),
                       label=math.floor((position * gap) + xaxix))
                  for position in range(10)]

        yticks = dict()
        colours = list()
        i = 0
        for vertex in self._vertex_in_question:
            index = self._vertex_in_question.index(vertex)
            offset = self._off_sets[index]
            yticks[offset] = "%s - %d" % (vertex.label, 0)
            counter = offset + vertex.n_atoms
            yticks[counter] = "%d" % vertex.n_atoms
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
                     'range': [0, self._max_y_value]},
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

        self._plot.set_options(options)
        if initial:
            for index in range(len(self._vertex_in_question)):
                true_index = (index * 2)
                self._plot.set_data(self._data_stores[true_index],
                                    self._data_stores[true_index+1])
            self._page.add(self._plot)
            self._page.show_all()
        self._page.queue_draw()

    def redraw(self, timer_tic):
        self._last_timer_tic = timer_tic
        if timer_tic <= ((self._runtime * 1000.0) /
                         self._machine_time_step):
            self._generate_plot(timer_tic, False)
            self._page.queue_draw()

    def recieved_spike(self, details):
        """
        translates the spike into a x and y axis and updates the data_store
        """
        for vert in self._vertex_in_question:
            for subvert in vert.subvertices:
                chip = subvert.placement.processor.chip
                processor = subvert.placement.processor
                if chip.get_coords()[0] == details['coords'][0] and \
                   chip.get_coords()[1] == details['coords'][1] and \
                   processor.idx == details['coords'][2] + 1:
                    logger.debug("Spike from %d, %d, %d, %d is from population"
                                 ".py %s" % (details['coords'][0],
                                             details['coords'][1],
                                             details['coords'][2] + 1,
                                             details['neuron_id'], vert.label))
                    self._update_data_store_with_spike(subvert,
                                                       details['neuron_id'],
                                                       details['time_in_ticks'])
        if self._do_fading:
            self._remove_stale_values(details['time_in_ticks'])

    def _update_data_store_with_spike(self, subvertex, local_neuron_id,
                                      time_in_tics):
        """
        modifies the data given and places data into data_store
        """
        #calcualte correct y axis
        index = self._vertex_in_question.index(subvertex.vertex)
        offset = self._off_sets[index]
        pop_neuron_id = subvertex.lo_atom + local_neuron_id
        offsetted_neuron_id = pop_neuron_id + offset
        #calculate correct x axis
        xaxix = (time_in_tics * self._machine_time_step) / 1000  # to ms
        true_index = (index * 2) + 1
        self._data_stores[true_index].append((xaxix, offsetted_neuron_id))

    def _remove_stale_values(self, time_in_tics):
        """
        remove all data points that are over the theshold ago
        """
        xaxix = (time_in_tics * self._machine_time_step) / 1000  # to ms
        for data_store_index in range(1, len(self._data_stores), 2):
            data = self._data_stores[data_store_index]
            for data_piece in data:
                if (xaxix - data_piece[0]) > int(self._x_axis_scope):
                    data.remove(data_piece)