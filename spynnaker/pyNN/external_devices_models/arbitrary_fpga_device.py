from pacman.model.graphs.application import ApplicationFPGAVertex
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)


class ArbitraryFPGADevice(
        ApplicationFPGAVertex, ProvidesKeyToAtomMappingImpl):
    __slots__ = []

    def __init__(
            self, n_neurons, fpga_link_id, fpga_id, board_address=None,
            label=None):
        # pylint: disable=too-many-arguments
        super(ArbitraryFPGADevice, self).__init__(
            n_neurons, fpga_id, fpga_link_id, board_address, label)
