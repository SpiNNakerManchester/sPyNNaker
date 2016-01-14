from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from spinn_front_end_common.interface.buffer_management.buffer_models.\
    abstract_receive_buffers_to_host import \
    AbstractReceiveBuffersToHost


class PopulationPartitionedVertex(
        PartitionedVertex, AbstractReceiveBuffersToHost):
    """ Represents a sub-set of atoms from a AbstractConstrainedVertex
    """

    def __init__(
            self, buffering_output, resources_required, label,
            constraints=None):
        """
        :param buffering_output: True if the vertex is set to buffer output,\
                    False otherwise
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
        AbstractReceiveBuffersToHost.__init__(self)
        PartitionedVertex.__init__(
            self, resources_required=resources_required, label=label,
            constraints=constraints)

        self._buffering_output = buffering_output

    def buffering_output(self):
        return self._buffering_output

    def is_receives_buffers_to_host(self):
        return True

