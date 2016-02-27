from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from spinn_front_end_common.interface.buffer_management.buffer_models\
    .receives_buffers_to_host_basic_impl import ReceiveBuffersToHostBasicImpl


class BufferedPartitionedVertex(
        PartitionedVertex, ReceiveBuffersToHostBasicImpl):
    """ Represents a Partitioned Vertex that is also buffered
    """

    def __init__(
            self, resources_required, label, constraints=None):
        """
        :param resources_required: The approximate resources needed for\
                    the vertex
        :type resources_required:\
                    :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :param label: The name of the subvertex
        :type label: str
        :param constraints: The constraints of the subvertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
        """
        PartitionedVertex.__init__(
            self, resources_required=resources_required, label=label,
            constraints=constraints)
        ReceiveBuffersToHostBasicImpl.__init__(self)
