from spynnaker.pyNN.models.abstract_models.component_vertex \
    import ComponentVertex
from pacman.structures.constraints.basic_placer_constraint \
    import BasicPlacerConstraint


class ExternalDevice(ComponentVertex):
    def __init__(self, n_neurons, virtual_chip_coords,
                 connected_node_coords, connected_node_edge, label=None):
        ComponentVertex.__init__(self, n_neurons=n_neurons, label=label)
        self.virtual_chip_coords = virtual_chip_coords
        self.connected_chip_coords = connected_node_coords
        self.connected_chip_edge = connected_node_edge
        placement_constraint = BasicPlacerConstraint(virtual_chip_coords['x'],
                                                     virtual_chip_coords['y'])
        self.add_constraint(placement_constraint)

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

    @staticmethod
    def split_into_subvertex_count():
        return 1
