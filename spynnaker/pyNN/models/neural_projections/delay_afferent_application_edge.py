from pacman.model.graph.application.simple_application_edge import \
    SimpleApplicationEdge
from spynnaker.pyNN.models.neural_projections.delay_afferent_machine_edge \
    import DelayAfferentMachineEdge


class DelayAfferentApplicationEdge(SimpleApplicationEdge):

    def __init__(self, prevertex, delayvertex, label=None):
        SimpleApplicationEdge.__init__(
            self, prevertex, delayvertex, label=label)

    def create_machine_edge(self, pre_vertex, post_vertex):
        """ Create a subedge between the pre_vertex and the post_vertex

        :param pre_vertex: The subvertex at the start of the subedge
        :type pre_vertex:\
            :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :param post_vertex: The subvertex at the end of the subedge
        :type post_vertex:\
            :py:class:`pacman.model.graph.application.abstract_application_vertex.AbstractApplicationVertex`
        :return: The created subedge
        """
        return DelayAfferentMachineEdge(pre_vertex, post_vertex)
