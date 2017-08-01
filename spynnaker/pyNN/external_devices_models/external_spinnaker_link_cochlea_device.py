from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from spinn_front_end_common.abstract_models.impl import \
    ProvidesKeyToAtomMappingImpl


class ExternalCochleaDevice(
        ApplicationSpiNNakerLinkVertex, ProvidesKeyToAtomMappingImpl):

    default_parameters = {
        'board_address': None,
        'label': "ExternalCochleaDevice"}

    def __init__(
            self, n_neurons,
            spinnaker_link,
            label=default_parameters['label'],
            board_address=default_parameters['board_address']):
        ApplicationSpiNNakerLinkVertex.__init__(
            self, n_atoms=n_neurons, spinnaker_link_id=spinnaker_link,
            label=label, max_atoms_per_core=n_neurons,
            board_address=board_address)
        ProvidesKeyToAtomMappingImpl.__init__(self)
