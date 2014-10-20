from spynnaker.pyNN.models.pynn_population import Population
from spynnaker.pyNN.visualiser_package.visualiser_vertex import VisualiserVertex
from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN import exceptions

from visualiser_framework.visualiser_constants import VISUALISER_MODES

from spinnman.constants import TRAFFIC_TYPE, CONNECTION_TYPE


class VisualisedVertex(Population):

    def __init__(self, size, cellclass, cellparams, spinnaker, label,
                 multi_cast_vertex=None, structure=None):

        Population.__init__(
            self, size, cellclass, cellparams, spinnaker, label,
            multi_cast_vertex=multi_cast_vertex, structure=structure)

    def record(
            self, to_file=None, receive_port_no=None, hostname=None,
            tag=None, traffic_type=TRAFFIC_TYPE.EIEIO,
            visualiser_mode=VISUALISER_MODES.RASTER,
            visualiser_2d_dimension=None, visualiser_raster_seperate=None,
            visualiser_no_colours=None, visualiser_average_period_tics=None,
            visualiser_longer_period_tics=None,
            visualiser_update_screen_in_tics=None,
            visualiser_reset_counters=None,
            visualiser_reset_counter_period=None):

        #add a visulaiser vertex to the list of vertex's to be visualised by
        # the visualiser
        connection_type = None
        if traffic_type == TRAFFIC_TYPE.EIEIO:
            connection_type = CONNECTION_TYPE.UDP_IPTAG
        elif traffic_type == TRAFFIC_TYPE.SDP:
            connection_type = CONNECTION_TYPE.SDP_IPTAG
        else:
            raise exceptions.ConfigurationException(
                "currently only EIEIO and SDP traffic is supported for "
                "visualisation")

        if conf.config.getboolean("Recording", "send_live_spikes"):
            # add an edge to the monitor
            #check to see if it needs to be created in the frist place
            if receive_port_no is None:
                receive_port_no = conf.config.getint("Recording",
                                                     "live_spike_port")
            if hostname is None:
                hostname = conf.config.get("Recording", "live_spike_host")

        visualiser_vertex = VisualiserVertex(
            visualiser_mode, visualiser_2d_dimension,
            visualiser_no_colours, visualiser_average_period_tics,
            visualiser_longer_period_tics,
            visualiser_update_screen_in_tics, visualiser_reset_counters,
            visualiser_reset_counter_period, visualiser_raster_seperate,
            self._vertex, receive_port_no, traffic_type, hostname,
            connection_type)
        self._spinnaker.add_visualiser_vertex(visualiser_vertex)
        self._vertex.set_record(True)

        if conf.config.getboolean("Recording", "send_live_spikes"):
        # set the iptag params for receiving said packets if live
            tag = conf.config.getint("Recording", "live_spike_tag")
            if tag is None:
                raise exceptions.ConfigurationException(
                    "Target tag for live spikes has not been set")
            self._spinnaker.add_edge_to_recorder_vertex(
                self._vertex, receive_port_no, hostname, tag)


