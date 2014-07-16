from spynnaker.pyNN.models.abstract_models.abstract_external_device import ExternalDevice


class AbstractExternalRetinaDevice(ExternalDevice):

    def __init__(self, n_neurons, virtual_chip_coords, connected_node_coords,
                 connected_node_edge, label=None):
        ExternalDevice.__init__(self, n_neurons, virtual_chip_coords,
                                connected_node_coords, connected_node_edge,
                                label=label)

    @property
    def requires_retina_page(self):
        return True
