from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.application import ApplicationEdge

from spynnaker.pyNN.models.neural_projections.projection_machine_edge \
    import ProjectionMachineEdge

import logging

logger = logging.getLogger(__name__)


class ProjectionApplicationEdge(ApplicationEdge):
    """ An edge which terminates on an AbstractPopulationVertex
    """

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, label=None):
        ApplicationEdge.__init__(
            self, pre_vertex, post_vertex, label=label)

        # A list of all synapse information for all the projections that are
        # represented by this edge
        self._synapse_information = [synapse_information]

        # The edge from the delay extension of the pre_vertex to the
        # post_vertex - this might be None if no long delays are present
        self._delay_edge = None

        self._stored_synaptic_data_from_machine = None

    def add_synapse_information(self, synapse_information):
        synapse_information.index = len(self._synapse_information)
        self._synapse_information.append(synapse_information)

    @property
    def synapse_information(self):
        return self._synapse_information

    @property
    def delay_edge(self):
        return self._delay_edge

    @delay_edge.setter
    def delay_edge(self, delay_edge):
        self._delay_edge = delay_edge

    @property
    def n_delay_stages(self):
        if self._delay_edge is None:
            return 0
        return self._delay_edge.pre_vertex.n_delay_stages

    @overrides(ApplicationEdge.create_machine_edge)
    def create_machine_edge(
            self, pre_vertex, post_vertex, label):
        return ProjectionMachineEdge(
            self._synapse_information, pre_vertex, post_vertex, label)
