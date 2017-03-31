from pacman.model.decorators.overrides import overrides
from spynnaker.pyNN.models.neural_projections.delayed_machine_edge \
    import DelayedMachineEdge
from pacman.model.graphs.application import ApplicationEdge


class DelayedApplicationEdge(ApplicationEdge):

    def __init__(
            self, pre_vertex, post_vertex, synapse_information, label=None):
        ApplicationEdge.__init__(
            self, pre_vertex, post_vertex, label=label)
        self._synapse_information = [synapse_information]

    def add_synapse_information(self, synapse_information):
        self._synapse_information.append(synapse_information)

    @overrides(ApplicationEdge.create_machine_edge)
    def create_machine_edge(self, pre_vertex, post_vertex, label):
        return DelayedMachineEdge(
            self._synapse_information, pre_vertex, post_vertex, label)
