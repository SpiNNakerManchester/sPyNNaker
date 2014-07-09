from spynnaker.pyNN.models.abstract_models.virtual_vertex import \
    VirtualVertex

class ExternalDevice(VirtualVertex):
    def __init__(self, n_neurons, virtual_chip_coords, connected_node_coords,
                 connected_node_edge, label=None):
        VirtualVertex.__init__(self, n_neurons, virtual_chip_coords,
                               connected_node_coords, connected_node_edge,
                               label=label)

    @property
    def model_name(self):
        return "ExternalDevice:{}".format(self.label)

    def get_maximum_atoms_per_core(self):
        raise NotImplementedError

    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
                                machine_time_step_us, partition_data_object):
        raise NotImplementedError