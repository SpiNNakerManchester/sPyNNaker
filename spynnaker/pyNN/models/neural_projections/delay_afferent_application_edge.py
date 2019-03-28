from pacman.model.graphs.application import ApplicationEdge
from .delay_afferent_machine_edge import DelayAfferentMachineEdge


class DelayAfferentApplicationEdge(ApplicationEdge):
    __slots__ = ()

    def __init__(self, prevertex, delayvertex, label=None):
        super(DelayAfferentApplicationEdge, self).__init__(
            prevertex, delayvertex, label=label)

    def create_machine_edge(self, pre_vertex, post_vertex, label):
        return DelayAfferentMachineEdge(pre_vertex, post_vertex, label)
