from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.models.abstract_models.abstract_partitionable_vertex \
    import AbstractPartitionableVertex


from pacman.model.constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource


from abc import ABCMeta
from six import add_metaclass
from spynnaker.pyNN.models.abstract_models.abstract_routerable_vertex import \
    AbstractRouterableVertex


@add_metaclass(ABCMeta)
class AbstractVirtualVertex(AbstractPartitionableVertex,
                            AbstractRecordableVertex, AbstractRouterableVertex):

    def __init__(self, n_neurons, virtual_chip_coords, connected_node_coords,
                 connected_node_edge, label, max_atoms_per_core):
        AbstractRecordableVertex.__init__(self, label)
        AbstractPartitionableVertex.__init__(self, n_neurons, label,
                                             max_atoms_per_core)
        AbstractRouterableVertex.__init__(self)
        #set up virtual data structures
        self._virtual_chip_coords = virtual_chip_coords
        self._connected_chip_coords = connected_node_coords
        self._connected_chip_edge = connected_node_edge

    @property
    def model_name(self):
        return "VirtualVertex:{}".format(self.label)

    def add_placement_constrants_to_subverts(self, subverts):
        for subvert in subverts:
            placement_constaint = \
                PlacerChipAndCoreConstraint(self.virtual_chip_coords['x'],
                                            self.virtual_chip_coords['y'])
            subvert.add_constraint(placement_constaint)

    #inhirrted from partitonable vertex
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return CPUCyclesPerTickResource(0)

    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        return SDRAMResource(0)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return DTCMResource(0)