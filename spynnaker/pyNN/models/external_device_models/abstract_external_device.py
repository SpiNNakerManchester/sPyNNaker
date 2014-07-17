from spynnaker.pyNN.models.abstract_models.abstract_virtual_vertex \
    import VirtualVertex
from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class ExternalDevice(VirtualVertex):
    def __init__(self, n_neurons, virtual_chip_coords, connected_node_coords,
                 connected_node_edge, label):
        VirtualVertex.__init__(self, n_neurons, virtual_chip_coords,
                               connected_node_coords, connected_node_edge,
                               label)

    @property
    def model_name(self):
        return "ExternalDevice:{}".format(self.label)

    def add_constraints_to_subverts(self, subverts):
        pass