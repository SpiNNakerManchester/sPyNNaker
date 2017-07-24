from spinn_front_end_common.utilities.connections import LiveEventConnection


# The maximum number of 32-bit keys that will fit in a packet
_MAX_FULL_KEYS_PER_PACKET = 63

# The maximum number of 16-bit keys that will fit in a packet
_MAX_HALF_KEYS_PER_PACKET = 127


class SpynnakerLiveSpikesConnection(LiveEventConnection):
    """ A connection for receiving and sending live spikes from and to\
        SpiNNaker
    """

    def __init__(self, receive_labels=None, send_labels=None, local_host=None,
                 local_port=19999,
                 live_packet_gather_label="LiveSpikeReceiver"):
        """

        :param receive_labels: Labels of population from which live spikes\
                    will be received.
        :type receive_labels: iterable of str
        :param send_labels: Labels of population to which live spikes will be\
                    sent
        :type send_labels: iterable of str
        :param local_host: Optional specification of the local hostname or\
                    ip address of the interface to listen on
        :type local_host: str
        :param local_port: Optional specification of the local port to listen\
                    on.  Must match the port that the toolchain will send the\
                    notification on (19999 by default)
        :type local_port: int

        """

        LiveEventConnection.__init__(
            self, live_packet_gather_label, receive_labels, send_labels,
            local_host, local_port)

    def send_spike(self, label, neuron_id, send_full_keys=False):
        """ Send a spike from a single neuron

        :param label: The label of the population from which the spike will\
                    originate
        :type label: str
        :param neuron_id: The id of the neuron sending a spike
        :type neuron_id: int
        :param send_full_keys: Determines whether to send full 32-bit keys,\
                    getting the key for each neuron from the database, or\
                    whether to send 16-bit neuron ids directly
        :type send_full_keys: bool
        """
        self.send_spikes(label, [neuron_id], send_full_keys)

    def send_spikes(self, label, neuron_ids, send_full_keys=False):
        """ Send a number of spikes

        :param label: The label of the population from which the spikes will\
                    originate
        :type label: str
        :param neuron_ids: array-like of neuron ids sending spikes
        :type neuron_ids: [int]
        :param send_full_keys: Determines whether to send full 32-bit keys,\
                    getting the key for each neuron from the database, or\
                    whether to send 16-bit neuron ids directly
        :type send_full_keys: bool
        """
        self.send_events(label, neuron_ids, send_full_keys)
