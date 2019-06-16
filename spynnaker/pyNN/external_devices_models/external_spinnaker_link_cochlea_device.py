from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)


class ExternalCochleaDevice(
        ApplicationSpiNNakerLinkVertex, ProvidesKeyToAtomMappingImpl):
    __slots__ = []

    def __init__(
            self, n_neurons, spinnaker_link, label=None, board_address=None):
        super(ExternalCochleaDevice, self).__init__(
            n_atoms=n_neurons, spinnaker_link_id=spinnaker_link,
            label=label, max_atoms_per_core=n_neurons,
            board_address=board_address)
