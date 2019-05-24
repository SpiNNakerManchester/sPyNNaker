from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationEdge
from .delayed_machine_edge import DelayedMachineEdge


class DelayedApplicationEdge(ApplicationEdge):
    __slots__ = [
        "__synapse_information"]

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, label=None):
        super(DelayedApplicationEdge, self).__init__(
            pre_vertex, post_vertex, label=label)
        self.__synapse_information = [synapse_information]

    @property
    def synapse_information(self):
        return self.__synapse_information

    def add_synapse_information(self, synapse_information):
        self.__synapse_information.append(synapse_information)

    @overrides(ApplicationEdge.create_machine_edge)
    def create_machine_edge(self, pre_vertex, post_vertex, label):
        return DelayedMachineEdge(
            self.__synapse_information, pre_vertex, post_vertex, label)
