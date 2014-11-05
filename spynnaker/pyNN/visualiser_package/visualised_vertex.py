from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.visualiser_package.visualiser_vertex import VisualiserVertex

from visualiser_framework import visualiser_constants


class VisualisedVertex(Population):

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 multi_cast_vertex=None, structure=None):

        Population.__init__(
            self, size, cellclass, cellparams, spinnaker, label,
            multi_cast_vertex=multi_cast_vertex, structure=structure)

    def record(
            self, to_file=None, visualiser_mode=visualiser_constants.RASTER,
            visualiser_2d_dimension=None, visualiser_raster_seperate=None,
            visualiser_no_colours=None, visualiser_average_period_tics=None,
            visualiser_longer_period_tics=None,
            visualiser_update_screen_in_tics=None,
            visualiser_reset_counters=None,
            visualiser_reset_counter_period=None):

        visualiser_vertex = VisualiserVertex(
            visualiser_mode, visualiser_2d_dimension,
            visualiser_raster_seperate, visualiser_no_colours,
            visualiser_average_period_tics, visualiser_longer_period_tics,
            visualiser_update_screen_in_tics, visualiser_reset_counters,
            visualiser_reset_counter_period, self._vertex)
        self._spinnaker.add_visualiser_vertex(visualiser_vertex)
        self._vertex.set_record(True)
        # set the file to store the spikes in once retrieved
        self._record_spike_file = to_file

        if conf.config.getboolean("Recording", "send_live_spikes"):
            # add an edge to the monitor
            self._spinnaker.add_edge_to_recorder_vertex(self._vertex)


