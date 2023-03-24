# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_front_end_common.utilities.connections import LiveEventConnection
from spinn_front_end_common.utilities.constants import NOTIFY_PORT

# The maximum number of 32-bit keys that will fit in a packet
_MAX_FULL_KEYS_PER_PACKET = 63
# The maximum number of 16-bit keys that will fit in a packet
_MAX_HALF_KEYS_PER_PACKET = 127


class SpynnakerLiveSpikesConnection(LiveEventConnection):
    """ A connection for receiving and sending live spikes from and to\
        SpiNNaker
    """
    __slots__ = []

    def __init__(self, receive_labels=None, send_labels=None, local_host=None,
                 local_port=NOTIFY_PORT,
                 live_packet_gather_label="LiveSpikeReceiver"):
        """
        :param iterable(str) receive_labels:
            Labels of population from which live spikes will be received.
        :param iterable(str) send_labels:
            Labels of population to which live spikes will be sent
        :param str local_host:
            Optional specification of the local hostname or IP address of the
            interface to listen on
        :param int local_port:
            Optional specification of the local port to listen on. Must match
            the port that the toolchain will send the notification on (19999
            by default)
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            live_packet_gather_label, receive_labels, send_labels,
            local_host, local_port)

    def send_spike(self, label, neuron_id, send_full_keys=False):
        """ Send a spike from a single neuron

        :param str label:
            The label of the population from which the spike will originate
        :param int neuron_id: The ID of the neuron sending a spike
        :param bool send_full_keys: Determines whether to send full 32-bit
            keys, getting the key for each neuron from the database, or
            whether to send 16-bit neuron IDs directly
        """
        self.send_spikes(label, [neuron_id], send_full_keys)

    def send_spikes(self, label, neuron_ids, send_full_keys=False):
        """ Send a number of spikes

        :param str label:
            The label of the population from which the spikes will originate
        :param list(int) neuron_ids: array-like of neuron IDs sending spikes
        :param bool send_full_keys: Determines whether to send full 32-bit
            keys, getting the key for each neuron from the database, or
            whether to send 16-bit neuron IDs directly
        """
        self.send_events(label, neuron_ids, send_full_keys)
