# general imports
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase

# pacman imports
from pacman.model.graphs.application import ApplicationFPGAVertex
from spinn_front_end_common.abstract_models.impl\
    import ProvidesKeyToAtomMappingImpl


@add_metaclass(AbstractBase)
class ArbitraryFPGADevice(
        ApplicationFPGAVertex, ProvidesKeyToAtomMappingImpl):

    default_parameters = {
        'board_address': None, 'label': "ArbitraryFPGADevice"}

    def __init__(
            self, n_neurons, fpga_link_id, fpga_id,
            board_address=default_parameters['board_address'],
            label=default_parameters['label']):
        # pylint: disable=too-many-arguments
        ApplicationFPGAVertex.__init__(
            self, n_neurons, fpga_id, fpga_link_id, board_address, label)
        ProvidesKeyToAtomMappingImpl.__init__(self)
