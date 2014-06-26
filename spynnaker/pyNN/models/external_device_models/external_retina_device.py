__author__ = 'stokesa6'
from pacman103.front.common.external_device import ExternalDevice
from pacman103.lib import data_spec_constants
from pacman103.core import exceptions
from pacman103.core.utilities import packet_conversions
import math

class ExternalRetinaDevice(ExternalDevice):
    core_app_identifier = \
        data_spec_constants.EXTERNAL_RETINA_DEVICE_CORE_APPLICATION_ID
    MANAGEMENT_BIT = 0x400
    LEFT_RETINA_ENABLE = 0x45
    RIGHT_RETINA_ENABLE = 0x46
    LEFT_RETINA_DISABLE = 0x45
    RIGHT_RETINA_DISABLE = 0x46
    LEFT_RETINA_KEY_SET = 0x43
    RIGHT_RETINA_KEY_SET = 0x44
    UP_POLARITY = "UP"
    DOWN_POLARITY = "DOWN"
    MERGED_POLARITY = "MERGED"

    LEFT_RETINA = "LEFT"
    RIGHT_RETINA = "RIGHT"


    def __init__( self, n_neurons, virtual_chip_coords,
                  connected_chip_coords, connected_chip_edge, position,
                  label=None, polarity=UP_POLARITY):
        super(ExternalRetinaDevice, self).__init__(128*128, # takes into account polarity
                                                   virtual_chip_coords,
                                                   connected_chip_coords,
                                                   connected_chip_edge,
                                                   label=label)
        self.position = position
        self.polarity = polarity
        start_processor = None
        if self.position == self.RIGHT_RETINA:
            if self.polarity == ExternalRetinaDevice.UP_POLARITY:
                self.constraints.p = 8
            else:
                self.constraints.p = 0
        elif self.position == self.LEFT_RETINA:
            if self.polarity == ExternalRetinaDevice.UP_POLARITY:
                self.constraints.p = 24
            else:
                self.constraints.p = 16
        else:
            raise exceptions.ConfigurationException("The external Retina does "
                                                    "not recognise this position")

        if self.polarity == ExternalRetinaDevice.MERGED_POLARITY:
            self.atoms = 128*128*2

    '''
    method that returns the commands for the retina external device
    '''
    def get_commands(self, last_runtime_tic):
        commands = list()

        #change the retina key it transmits with (based off if its right or left
        if self.position == self.RIGHT_RETINA:
            mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                       self.virtual_chip_coords['y'] << 16 | \
                       self.MANAGEMENT_BIT | self.RIGHT_RETINA_KEY_SET
        else:
            mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                       self.virtual_chip_coords['y'] << 16 | \
                       self.MANAGEMENT_BIT | self.LEFT_RETINA_KEY_SET

        #to ensure populations receive the correct packets, this needs to be
        #different bsed on which retina
        if self.position == self.RIGHT_RETINA:
            mgmt_payload = 0 << 24 | 6 << 16
        else:
            mgmt_payload = 0 << 24 | 7 << 16

        command = {'t': 0, "cp": 1, 'key': mgmt_key, 'payload': mgmt_payload,
                   'repeat': 5, 'delay': 1000}
        commands.append(command)

        #make retina enabled (dependant on if its a left or right retina
        if self.position == self.RIGHT_RETINA:
            mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                       self.virtual_chip_coords['y'] << 16 | \
                       self.MANAGEMENT_BIT | self.RIGHT_RETINA_ENABLE # enable
        else:
            mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                       self.virtual_chip_coords['y'] << 16 | \
                       self.MANAGEMENT_BIT | self.LEFT_RETINA_ENABLE # enable
        mgmt_payload = 1
        command = {'t': 0, "cp": 1, 'key': mgmt_key, 'payload': mgmt_payload,
                   'repeat': 5, 'delay': 1000}
        commands.append(command)

        # disable retina
        if self.position == self.RIGHT_RETINA:
            mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                       self.virtual_chip_coords['y'] << 16 | \
                       self.MANAGEMENT_BIT | self.RIGHT_RETINA_DISABLE
        else:
            mgmt_key = self.virtual_chip_coords['x'] << 24 | \
                       self.virtual_chip_coords['y'] << 16 | \
                       self.MANAGEMENT_BIT | self.LEFT_RETINA_DISABLE
        mgmt_payload = 0
        command = {'t': last_runtime_tic, "cp": 1, 'key': mgmt_key,
                   'payload': mgmt_payload, 'repeat': 5, 'delay': 1000}
        commands.append(command)
        return commands

    '''
    over loads the generate routing info for virtual key space
    each retina has its own unique outgoing key
    '''
    def generate_routing_info(self, subedge):
        processor_id = subedge.presubvertex.placement.processor.idx % 16
        if self.position == self.RIGHT_RETINA:
            if self.polarity == ExternalRetinaDevice.UP_POLARITY:
                part_1 = packet_conversions.get_key_from_coords(0, 6, processor_id)
                key = part_1 | (1 << 14)
                return key, 0xffff7800
            else:
                key = packet_conversions.get_key_from_coords(0, 6, processor_id)
                return key, 0xffff7800
        else:
            if self.polarity == ExternalRetinaDevice.UP_POLARITY:
                key = packet_conversions.get_key_from_coords(0, 7, processor_id) | (1 << 14)
                return key, 0xffff7800
            else:
                key = packet_conversions.get_key_from_coords(0, 7, processor_id)
                return key, 0xffff7800

    '''
    overloaded as retinas require command packets to start, disable, and set key
    '''
    def requires_multi_cast_source(self):
        return True

    def split_into_subvertex_count(self):
        return self.atoms >> 11 # keys available for neuron id

    def get_maximum_atoms_per_core(self):
        return math.floor(float(self.atoms) /
                          float(self.split_into_subvertex_count()))

    @property
    def model_name(self):
        return "external retina device at " \
               "position {} and polarity {}".format(self.position,
                                                    self.polarity)

    @property
    def requires_retina_page(self):
        '''
        used by the visuliser to determine if a retina page should be used
        '''
        return True

    def get_packet_retina_coords(self, details, mode):
        return packet_conversions.get_x_from_robot_retina(details), \
               packet_conversions.get_y_from_robot_retina(details), \
               packet_conversions.get_spike_value_from_robot_retina(details)
