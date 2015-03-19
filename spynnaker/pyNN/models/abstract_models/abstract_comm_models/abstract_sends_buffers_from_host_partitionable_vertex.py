from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod
from pacman.model.abstract_classes.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman.model.constraints.tag_allocator_constraints.\
    tag_allocator_require_iptag_constraint import \
    TagAllocatorRequireIptagConstraint


@add_metaclass(ABCMeta)
class AbstractSendsBuffersFromHostPartitionableVertex(
        AbstractPartitionableVertex):

    def __init__(self, n_atoms, label, constraints, max_atoms_per_core, tag,
                 port, address):
        AbstractPartitionableVertex.__init__(
            self, n_atoms=n_atoms, label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)
        self.add_constraint(TagAllocatorRequireIptagConstraint(
            address, port, strip_sdp=True, tag_id=tag))

    @abstractmethod
    def is_sends_buffers_from_host_partitionable_vertex(self):
        """helper method for is instance

        :return:
        """
