from spynnaker.pyNN.models.abstract_models.abstract_component_vertex import \
    ComponentVertex
from pacman.model.graph.vertex import Vertex
from pacman.model.constraints.placer_chip_and_core_constraint import \
    PlacerChipAndCoreConstraint
from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource
from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class VirtualVertex(Vertex, ComponentVertex):

    def __init__(self, n_neurons, virtual_chip_coords, connected_node_coords,
                 connected_node_edge, label):
        ComponentVertex.__init__(self, label)
        Vertex.__init__(self, n_neurons, label)
        #set up virtual data structures
        self.virtual_chip_coords = virtual_chip_coords
        self.connected_chip_coords = connected_node_coords
        self.connected_chip_edge = connected_node_edge
        placement_constaint = \
            PlacerChipAndCoreConstraint(virtual_chip_coords['x'],
                                        virtual_chip_coords['y'])
        self.add_constraint(placement_constaint)

    @property
    def model_name(self):
        return "VirtualVertex:{}".format(self.label)

    def get_resources_used_by_atoms(self, lo_atom, hi_atom,
                                    no_machine_time_steps):
        resources = list()
        # noinspection PyTypeChecker
        resources.append(CPUCyclesPerTickResource(0))
        resources.append(DTCMResource(0))
        resources.append(SDRAMResource(0))
        return resources