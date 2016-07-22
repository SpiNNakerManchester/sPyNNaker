from pacman.model.graph.application.simple_application_edge import \
    SimpleApplicationEdge
from spynnaker.pyNN.models.neural_projections.delay_afferent_machine_edge \
    import DelayAfferentMachineEdge


class DelayAfferentApplicationEdge(SimpleApplicationEdge):

    def __init__(self, prevertex, delayvertex, label=None):
        SimpleApplicationEdge.__init__(
            self, prevertex, delayvertex, label=label)

    def create_machine_edge(self, pre_vertex, post_vertex):
        return DelayAfferentMachineEdge(pre_vertex, post_vertex)
