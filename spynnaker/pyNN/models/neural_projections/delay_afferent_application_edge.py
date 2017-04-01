from pacman.model.graphs.application import ApplicationEdge
from spynnaker.pyNN.models.neural_projections.delay_afferent_machine_edge \
    import DelayAfferentMachineEdge


class DelayAfferentApplicationEdge(ApplicationEdge):

    def __init__(self, prevertex, delayvertex, label=None):
        ApplicationEdge.__init__(
            self, prevertex, delayvertex, label=label)

    def create_machine_edge(self, pre_vertex, post_vertex, label):
        return DelayAfferentMachineEdge(pre_vertex, post_vertex, label)
