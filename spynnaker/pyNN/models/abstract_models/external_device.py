from pacman103.front.common.component_vertex import ComponentVertex
from pacman103.core import exceptions
from pacman103.lib.lib_map import VertexConstraints
from pacman103.lib import data_spec_constants

import os

class ExternalDevice(ComponentVertex):
    def __init__( self, n_neurons, virtual_chip_coords,
                  connected_node_coords, connected_node_edge, label=None):
        super(ExternalDevice , self ).__init__(n_neurons=n_neurons, label=label,
                                               virtual=True)
        self.virtual_chip_coords = virtual_chip_coords
        self.connected_chip_coords = connected_node_coords
        self.connected_chip_edge = connected_node_edge
        placementConstraint = VertexConstraints(x=None, y=None)
        placementConstraint.x = virtual_chip_coords['x']
        placementConstraint.y = virtual_chip_coords['y']
        self.constraints = placementConstraint

    @property
    def model_name(self):
        return "ExternalDevice:{}".format(self.label)

    def get_maximum_atoms_per_core(self):
        raise NotImplementedError

    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
                                machine_time_step_us, partition_data_object):
        raise NotImplementedError

    @property
    def requires_retina_page(self):
        return False

    def split_into_subvertex_count(self):
        return 1
