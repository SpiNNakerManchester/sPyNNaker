from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint


@add_metaclass(ABCMeta)
class AbstractVirtualVertex(AbstractPartitionableVertex):

    def __init__(self, n_atoms, virtual_chip_x, virtual_chip_y,
                 connected_to_real_chip_x, connected_to_real_chip_y,
                 connected_to_real_chip_link_id, label, max_atoms_per_core):

        AbstractPartitionableVertex.__init__(self, n_atoms, label,
                                             max_atoms_per_core)
        # set up virtual data structures
        self._virtual_chip_x = virtual_chip_x
        self._virtual_chip_y = virtual_chip_y
        self._connected_to_real_chip_x = connected_to_real_chip_x
        self._connected_to_real_chip_y = connected_to_real_chip_y
        self._connected_to_real_chip_link_id = connected_to_real_chip_link_id

        placement_constaint = \
            PlacerChipAndCoreConstraint(self._virtual_chip_x,
                                        self._virtual_chip_y)
        self.add_constraint(placement_constaint)

    @property
    def virtual_chip_x(self):
        return self._virtual_chip_x

    @property
    def virtual_chip_y(self):
        return self._virtual_chip_y

    @property
    def connected_to_real_chip_x(self):
        return self._connected_to_real_chip_x

    @property
    def connected_to_real_chip_y(self):
        return self._connected_to_real_chip_y

    @property
    def connected_to_real_chip_link_id(self):
        return self._connected_to_real_chip_link_id

    @abstractmethod
    def is_virtual_vertex(self):
        """ helper method for is instance

        :return:
        """

    # overlaoded method from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        return 0

    # overlaoded method from partitionable vertex
    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        return 0

    # overlaoded method from partitionable vertex
    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        return 0
