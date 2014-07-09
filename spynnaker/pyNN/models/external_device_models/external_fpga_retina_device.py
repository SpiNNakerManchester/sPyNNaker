__author__ = 'stokesa6'
from spynnaker.pyNN.models.abstract_models.external_device import ExternalDevice
from spynnaker.pyNN.utilities.core.utilities import packet_conversions
from pacman103.lib import lib_map
from pacman103.core import exceptions
import os


class ExternalFPGARetinaDevice(ExternalDevice):

    UP_POLARITY = "UP"
    DOWN_POLARITY = "DOWN"
    MERGED_POLARITY = "MERGED"
    MODE_128 = "128"
    MODE_64 = "64"
    MODE_32 = "32"
    MODE_16 = "16"

    def __init__( self, mode, virtual_chip_coords,
                  connected_chip_coords, connected_chip_edge, polarity,
                  label=None):

        if mode == ExternalFPGARetinaDevice.MODE_128:
            if (self.polarity == ExternalFPGARetinaDevice.UP_POLARITY or
                self.polarity == ExternalFPGARetinaDevice.DOWN_POLARITY):
                n_neurons = 128 * 128
            else:
                n_neurons = 128 * 128 * 2
        elif mode == ExternalFPGARetinaDevice.MODE_64:
            if (self.polarity == ExternalFPGARetinaDevice.UP_POLARITY or
                self.polarity == ExternalFPGARetinaDevice.DOWN_POLARITY):
                n_neurons = 64 * 64
            else:
                n_neurons = 64 * 64 * 2
        elif mode == ExternalFPGARetinaDevice.MODE_32:
            if (self.polarity == ExternalFPGARetinaDevice.UP_POLARITY or
                self.polarity == ExternalFPGARetinaDevice.DOWN_POLARITY):
                n_neurons = 32 * 32
            else:
                n_neurons = 32 * 32 * 2
        elif mode == ExternalFPGARetinaDevice.MODE_16:
            if (self.polarity == ExternalFPGARetinaDevice.UP_POLARITY or
                self.polarity == ExternalFPGARetinaDevice.DOWN_POLARITY):
                n_neurons = 16 * 16
            else:
                n_neurons = 16 * 16 * 2
        else:
            raise exceptions.ConfigurationException("the FPGA retina does not "
                                                    "recongise this mode")
        super(ExternalFPGARetinaDevice, self).__init__(n_neurons,
                                                       virtual_chip_coords,
                                                       connected_chip_coords,
                                                       connected_chip_edge,
                                                       label=label)
        self.polarity = polarity
        if self.polarity == ExternalFPGARetinaDevice.UP_POLARITY:
            self.constraints.p = 8
        else:
            self.constraints.p = 0


    '''
    method that returns the commands for the retina external device
    '''
    def get_commands(self, last_runtime_tic):
        commands = list()

        mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                   self.virtual_chip_coords['y']+1 << 16 | 0xffff

        mgmt_payload = 1
        command = {'t': 0, "cp": 1, 'key': mgmt_key, 'payload': mgmt_payload,
                   'repeat': 5, 'delay': 100}
        commands.append(command)

        mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                   self.virtual_chip_coords['y']+1 << 16 | 0xfffe
        mgmt_payload = 0
        command = {'t': last_runtime_tic, "cp": 1, 'key': mgmt_key, 'payload': mgmt_payload,
                   'repeat': 5, 'delay': 100}
        commands.append(command)
        return commands

    '''
    over writes component method, return the key and mask
    '''
    def generate_routing_info(self, subedge):
        if self.polarity is None:
            key = self.virtual_chip_coords['x'] << 24 | \
                  self.virtual_chip_coords['y'] << 16
            mask = 0xffff0000
            return key, mask
        elif self.polarity == ExternalFPGARetinaDevice.UP_POLARITY:
            key = self.virtual_chip_coords['x'] << 24 | \
                  self.virtual_chip_coords['y'] << 16 | \
                  1 << 14
            mask = 0xffffC000
            return key, mask
        elif self.polarity == ExternalFPGARetinaDevice.DOWN_POLARITY:
            key = self.virtual_chip_coords['x'] << 24 | \
                  self.virtual_chip_coords['y'] << 16
            mask = 0xffffC000
            return key, mask
        else:
            raise exceptions.ConfigurationException("The FPGA retina requires the poloarity "
                                                    "parameter to either be UP, DOWN or None. "
                                                    "Other values result in the Model not knowing "
                                                    "how to initlise its key and mask.")



    '''
    overloded method to add a mulit-cast soruce
    '''
    def requires_multi_cast_source(self):
        return True

    '''
    name for debugs
    '''
    @property
    def model_name(self):
        return "external FPGA retina device"

    def requires_retina_page(self):
        '''
        used by the visuliser to determine if a retina page should be used
        '''
        return True

    @staticmethod
    def get_packet_retina_coords(self, details, mode):
        return packet_conversions.get_x_from_fpga_retina(details, mode), \
               packet_conversions.get_y_from_fpga_retina(details, mode), \
               packet_conversions.get_spike_value_from_fpga_retina(details,
                                                                   mode)


    def split_into_subvertex_count(self):
        if (self.atoms >> 11) <= 0:  # if the keys dont touce p,
                                     # then just 1 subvert is needed
            return 1
        else:
            return self.atoms >> 11 # keys available for neuron id

