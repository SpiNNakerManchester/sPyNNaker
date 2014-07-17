__author__ = 'stokesa6'
from spynnaker.pyNN.models.external_device_models.\
    abstract_external_retina_device import AbstractExternalRetinaDevice
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN import exceptions


class ExternalFPGARetinaDevice(AbstractExternalRetinaDevice):

    MODE_128 = "128"
    MODE_64 = "64"
    MODE_32 = "32"
    MODE_16 = "16"

    def __init__(self, mode, virtual_chip_coords, connected_chip_coords,
                 connected_chip_edge, polarity, label=None):

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

        AbstractExternalRetinaDevice.__init__(self, n_neurons,
                                              virtual_chip_coords,
                                              connected_chip_coords,
                                              connected_chip_edge,
                                              label=label)

    def get_commands(self, last_runtime_tic):
        """
        method that returns the commands for the retina external device
        """
        commands = list()

        mgmt_key = \
            self.virtual_chip_coords['x'] << 24 | \
            self.virtual_chip_coords['y'] + 1 << 16 | 0xffff

        mgmt_payload = 1
        command = {'t': 0, "cp": 1, 'key': mgmt_key, 'payload': mgmt_payload,
                   'repeat': 5, 'delay': 100}
        commands.append(command)

        mgmt_key = \
            self.virtual_chip_coords['x'] << 24 | \
            self.virtual_chip_coords['y'] + 1 << 16 | 0xfffe
        mgmt_payload = 0
        command = {'t': last_runtime_tic, "cp": 1, 'key': mgmt_key,
                   'payload': mgmt_payload, 'repeat': 5, 'delay': 100}
        commands.append(command)
        return commands

    def generate_routing_info(self, subedge):
        """
        over writes component method, return the key and mask
        """
        if self.polarity is None:
            key = \
                self.virtual_chip_coords['x'] << 24 | \
                self.virtual_chip_coords['y'] << 16
            mask = 0xffff0000
            return key, mask
        elif self.polarity == ExternalFPGARetinaDevice.UP_POLARITY:
            key = \
                self.virtual_chip_coords['x'] << 24 | \
                self.virtual_chip_coords['y'] << 16 | \
                1 << 14
            mask = 0xffffC000
            return key, mask
        elif self.polarity == ExternalFPGARetinaDevice.DOWN_POLARITY:
            key = \
                self.virtual_chip_coords['x'] << 24 | \
                self.virtual_chip_coords['y'] << 16
            mask = 0xffffC000
            return key, mask
        else:
            raise exceptions.ConfigurationException(
                "The FPGA retina requires the poloarity parameter to either be "
                "UP, DOWN or None. Other values result in the Model not "
                "knowing how to initlise its key and mask.")

    @property
    def model_name(self):
        """
        name for debugs
        """
        return "external FPGA retina device"

    @staticmethod
    def get_packet_retina_coords(details, mode):
        return packet_conversions.get_x_from_fpga_retina(details, mode), \
            packet_conversions.get_y_from_fpga_retina(details, mode), \
            packet_conversions.get_spike_value_from_fpga_retina(details,
                                                                mode)


def requires_retina_page():
    """
    used by the visuliser to determine if a retina page should be used
    """
    return True