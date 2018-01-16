from spinn_front_end_common.utilities.connections import LiveEventConnection
from spinnman.messages.eieio import EIEIOType
from data_specification.enums import DataType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from pacman.model.decorators.overrides import overrides
from spinnman.messages.eieio.data_messages import EIEIODataMessage

_MAX_RATES_PER_PACKET = 32


class SpynnakerPoissonControlConnection(LiveEventConnection):
    __slots__ = [
        "_control_label_extension"]

    def __init__(
            self, poisson_labels=None, local_host=None, local_port=19999,
            control_label_extension="_control"):
        """

        :param poisson_labels: Labels of Poisson populations to be controlled
        :type poisson_labels: iterable of str
        :param local_host: Optional specification of the local hostname or\
                    ip address of the interface to listen on
        :type local_host: str
        :param local_port: Optional specification of the local port to listen\
                    on.  Must match the port that the toolchain will send the\
                    notification on (19999 by default)
        :type local_port: int
        :param control_label_extension:\
            The extra name added to the label of each Poisson source
        :type control_label_extension: str

        """
        control_labels = [
            "{}{}".format(label, control_label_extension)
            for label in poisson_labels
        ]

        super(SpynnakerPoissonControlConnection, self).__init__(
            live_packet_gather_label=None, send_labels=control_labels,
            local_host=local_host, local_port=local_port)

        self._control_label_extension = control_label_extension

    def _control_label(self, label):
        return "{}{}".format(label, self._control_label_extension)

    @overrides(LiveEventConnection.add_start_callback)
    def add_start_callback(self, label, start_callback):
        super(SpynnakerPoissonControlConnection, self).add_start_callback(
            self._control_label(label), start_callback)

    @overrides(LiveEventConnection.add_init_callback)
    def add_init_callback(self, label, init_callback):
        super(SpynnakerPoissonControlConnection, self).add_init_callback(
            self._control_label(label), init_callback)

    @overrides(LiveEventConnection.add_receive_callback)
    def add_receive_callback(self, label, live_event_callback):
        raise ConfigurationException(
            "SpynnakerPoissonControlPopulation can't receive data")

    def set_rate(self, label, neuron_id, rate):
        """ Set the rate of a Poisson neuron within a Poisson source

        :param label: The label of the Population to set the rates of
        :param neuron_id: The neuron id to set the rate of
        :param rate: The rate to set in Hz
        """
        control_label = label
        if not control_label.endswith(self._control_label_extension):
            control_label = self._control_label(label)
        self.set_rates(control_label, [(neuron_id, rate)])

    def set_rates(self, label, neuron_id_rates):
        """ Set the rates of multiple Poisson neurons within a Poisson source

        :param label: The label of the Population to set the rates of
        :param neuron_id_rates: A list of tuples of (neuron id, rate) to be set
        """
        control_label = label
        if not control_label.endswith(self._control_label_extension):
            control_label = self._control_label(label)
        pos = 0
        while pos < len(neuron_id_rates):
            message, pos = self._assemble_message(
                self._atom_id_to_key[control_label], neuron_id_rates, pos)
            ip_address, port = self._send_address_details[control_label]
            self._sender_connection.send_eieio_message_to(
                message, ip_address, port)

    @staticmethod
    def _assemble_message(id_to_key_map, neuron_id_rates, pos):
        scale = DataType.S1615.scale  # @UndefinedVariable
        message = EIEIODataMessage.create(EIEIOType.KEY_PAYLOAD_32_BIT)
        for _ in range(_MAX_RATES_PER_PACKET):
            neuron_id, rate = neuron_id_rates[pos]
            key = id_to_key_map[neuron_id]
            message.add_key_and_payload(key, int(round(rate * scale)))
            pos += 1
            if pos >= len(neuron_id_rates):
                break
        return message, pos
