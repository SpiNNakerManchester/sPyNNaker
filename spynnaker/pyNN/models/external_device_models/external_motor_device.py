__author__ = 'stokesa6'
from pacman103.front.common.external_device import ExternalDevice
from pacman103.lib import data_spec_gen, data_spec_constants
from pacman103.lib import lib_map
from pacman103.core import exceptions
import os

class ExternalMotorDevice(ExternalDevice):
    core_app_identifier = \
        data_spec_constants.EXTERNAL_MOTER_DEVICE_CORE_APPLICATION_ID
    MANAGEMENT_BIT = 0x400
    RATE_CODING_ACTUATORS_ENABLE = 0x40

    def __init__( self, n_neurons, virtual_chip_coords,
                  connected_chip_coords, connected_chip_edge, label=None,
                  neuron_controlled = True):
        super(ExternalMotorDevice, self).__init__(n_neurons,
                                                  virtual_chip_coords,
                                                  connected_chip_coords,
                                                  connected_chip_edge,
                                                  label=label)
        self.neuron_controlled = neuron_controlled

    @property
    def model_name(self):
        return "external motor device"

    def get_commands(self, last_runtime_tic):
        return list()

    def split_into_subvertex_count(self):
        return 1