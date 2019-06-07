import logging
from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationEdge
from .projection_machine_edge import ProjectionMachineEdge

logger = logging.getLogger(__name__)


class ProjectionApplicationEdge(ApplicationEdge):
    """ An edge which terminates on an :py:class:`AbstractPopulationVertex`.
    """
    __slots__ = [
        "__delay_edge",
        "__stored_synaptic_data_from_machine",
        "__synapse_information"]

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, label=None):
        super(ProjectionApplicationEdge, self).__init__(
            pre_vertex, post_vertex, label=label)

        # A list of all synapse information for all the projections that are
        # represented by this edge
        self.__synapse_information = [synapse_information]

        # The edge from the delay extension of the pre_vertex to the
        # post_vertex - this might be None if no long delays are present
        self.__delay_edge = None

        self.__stored_synaptic_data_from_machine = None

    def add_synapse_information(self, synapse_information):
        synapse_information.index = len(self.__synapse_information)
        self.__synapse_information.append(synapse_information)

    @property
    def synapse_information(self):
        return self.__synapse_information

    @property
    def delay_edge(self):
        return self.__delay_edge

    @delay_edge.setter
    def delay_edge(self, delay_edge):
        self.__delay_edge = delay_edge

    @property
    def n_delay_stages(self):
        if self.__delay_edge is None:
            return 0
        return self.__delay_edge.pre_vertex.n_delay_stages

    @overrides(ApplicationEdge.create_machine_edge)
    def create_machine_edge(
            self, pre_vertex, post_vertex, label):
        return ProjectionMachineEdge(
            self.__synapse_information, pre_vertex, post_vertex, label)
