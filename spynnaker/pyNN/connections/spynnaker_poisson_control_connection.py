from spinn_front_end_common.utilities.connections.live_event_connection\
    import LiveEventConnection

from spinnman.messages.eieio.eieio_type import EIEIOType
from data_specification.enums.data_type import DataType
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinnman.messages.eieio.data_messages.eieio_data_message \
    import EIEIODataMessage

_MAX_RATES_PER_PACKET = 32


class SpynnakerPoissonControlConnection(LiveEventConnection):

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

        LiveEventConnection.__init__(
            self, live_packet_gather_label=None, send_labels=control_labels,
            local_host=local_host, local_port=local_port)

        self._control_label_extension = control_label_extension

    def _control_label(self, label):
        return "{}{}".format(label, self._control_label_extension)

    def add_start_callback(self, label, start_callback):
        control_label = self._control_label(label)
        LiveEventConnection.add_start_callback(
            self, control_label, start_callback)

    def add_init_callback(self, label, init_callback):
        control_label = self._control_label(label)
        LiveEventConnection.add_init_callback(
            self, control_label, init_callback)

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
        max_keys = _MAX_RATES_PER_PACKET

        pos = 0
        while pos < len(neuron_id_rates):

            message = EIEIODataMessage.create(EIEIOType.KEY_PAYLOAD_32_BIT)

            events_in_packet = 0
            while pos < len(neuron_id_rates) and events_in_packet < max_keys:
                (neuron_id, rate) = neuron_id_rates[pos]
                key = self._atom_id_to_key[control_label][neuron_id]
                rate_accum = int(round(rate / DataType.S1615.scale))
                message.add_key_and_payload(key, rate_accum)
                pos += 1
                events_in_packet += 1
            ip_address, port = self._send_address_details[control_label]
            self._sender_connection.send_eieio_message_to(
                message, ip_address, port)
