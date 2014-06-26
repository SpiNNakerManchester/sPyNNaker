__author__ = 'stokesa6'
from pacman103.front.common.external_device import ExternalDevice
from pacman103.lib import data_spec_constants, data_spec_gen
from pacman103.lib import lib_map
from pacman103.core import exceptions
import os



class ExternalCochleaDevice(ExternalDevice):
    core_app_identifier = \
        data_spec_constants.EXTERNAL_COCHLEA_DEVICE_CORE_APPLICATION_ID

    def __init__(self, n_neurons, virtual_chip_coords,
                 connected_chip_coords, connected_chip_edge, label=None):
        super(ExternalCochleaDevice, self).__init__(n_neurons,
                                                    virtual_chip_coords,
                                                    connected_chip_coords,
                                                    connected_chip_edge,
                                                    label=label)
