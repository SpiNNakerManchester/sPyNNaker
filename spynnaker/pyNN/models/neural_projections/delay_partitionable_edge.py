# spynnaker imports
from spynnaker.pyNN.models.neural_projections.projection_partitionable_edge \
    import ProjectionPartitionableEdge
from spynnaker.pyNN.models.neural_projections.delay_partitioned_edge \
    import DelayPartitionedEdge
from spynnaker.pyNN.utilities import conf


# spinn front end common imports
from pacman.utilities.utility_objs.timer import Timer

# pacman imports
from pacman.utilities.utility_objs.progress_bar import ProgressBar

# general imports
import math
import logging
import copy


logger = logging.getLogger(__name__)


class DelayPartitionableEdge(ProjectionPartitionableEdge):

    def __init__(self, presynaptic_population, postsynaptic_population,
                 machine_time_step, num_delay_stages, max_delay_per_neuron,
                 connector=None, synapse_list=None, synapse_dynamics=None,
                 label=None):
        ProjectionPartitionableEdge.__init__(self,
                                             presynaptic_population,
                                             postsynaptic_population,
                                             machine_time_step,
                                             connector=connector,
                                             synapse_list=synapse_list,
                                             synapse_dynamics=synapse_dynamics,
                                             label=label)
        self._pre_vertex = presynaptic_population._internal_delay_vertex
        self._stored_synaptic_data_from_machine = None

    @property
    def num_delay_stages(self):
        return self._pre_vertex.max_stages

    @property
    def max_delay_per_neuron(self):
        return self._pre_vertex.max_delay_per_neuron

    def _get_delay_stage_max_n_words(self, vertex_slice, stage):
        min_delay = ((stage + 1) * self.max_delay_per_neuron) + 1
        max_delay = min_delay + self.max_delay_per_neuron
        conns = self.synapse_list.get_max_n_connections(
            vertex_slice=vertex_slice, lo_delay=min_delay, hi_delay=max_delay)
        return conns

    def get_max_n_words(self, vertex_slice=None):
        """ Get the maximum number of words for a subvertex at the end of the\
            connection

        :param vertex_slice: the vertex slice which represents which part
                             of the partitionable vertex
        :type vertex_slice: pacman.model.graph_mapper.slide
        """
        return max([self._get_delay_stage_max_n_words(vertex_slice, stage)
                    for stage in range(self._pre_vertex.max_stages)])

    def get_n_rows(self):
        """ Get the number of synaptic rows coming in to a vertex at the end\
            of the connection
        """
        return self._synapse_list.get_n_rows() * self._pre_vertex.max_stages

    def create_subedge(self, presubvertex, postsubvertex, label=None):
        """ Create a subedge from this edge
        :param postsubvertex:
        :param presubvertex:
        :param label:
        """
        return DelayPartitionedEdge(presubvertex, postsubvertex)

    def get_synaptic_list_from_machine(self, graph_mapper, partitioned_graph,
                                       placements, transceiver, routing_infos):
        """ Get synaptic data for all connections in this Projection from the\
            machine.
        :param graph_mapper:
        :param partitioned_graph:
        :param placements:
        :param transceiver:
        :param routing_infos:
        :return:
        """
        if self._stored_synaptic_data_from_machine is None:
            timer = None
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer = Timer()
                timer.start_timing()

            subedges = \
                graph_mapper.get_partitioned_edges_from_partitionable_edge(
                    self)
            if subedges is None:
                subedges = list()

            synaptic_list = copy.copy(self._synapse_list)
            synaptic_list_rows = synaptic_list.get_rows()
            progress_bar = ProgressBar(
                len(subedges),
                "Reading back synaptic matrix for delayed edge between"
                " {} and {}".format(self._pre_vertex.label,
                                    self._post_vertex.label))
            for subedge in subedges:
                n_rows = subedge.get_n_rows(graph_mapper)
                pre_vertex_slice = \
                    graph_mapper.get_subvertex_slice(subedge.pre_subvertex)
                post_vertex_slice = \
                    graph_mapper.get_subvertex_slice(subedge.post_subvertex)

                sub_edge_post_vertex = \
                    graph_mapper.get_vertex_from_subvertex(
                        subedge.post_subvertex)
                rows = sub_edge_post_vertex.get_synaptic_list_from_machine(
                    placements, transceiver, subedge.pre_subvertex, n_rows,
                    subedge.post_subvertex,
                    self._synapse_row_io, partitioned_graph,
                    routing_infos, subedge.weight_scales).get_rows()

                for i in range(len(rows)):
                    delay_stage = math.floor(
                        float(i) / float(pre_vertex_slice.n_atoms)) + 1
                    min_delay = (delay_stage *
                                 self.pre_vertex.max_delay_per_neuron)
                    max_delay = (min_delay +
                                 self.pre_vertex.max_delay_per_neuron - 1)
                    synaptic_list_rows[
                        (i % pre_vertex_slice.n_atoms) +
                        pre_vertex_slice.lo_atom].set_slice_values(
                            rows[i], post_vertex_slice, min_delay, max_delay)
                progress_bar.update()
            progress_bar.end()
            self._stored_synaptic_data_from_machine = synaptic_list

            if conf.config.getboolean("Reports", "outputTimesForSections"):
                logger.info("Time to read matrix: {}".format(
                    timer.take_sample()))

        return self._stored_synaptic_data_from_machine
