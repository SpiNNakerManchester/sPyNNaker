# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_front_end_common.utilities.connections import LiveEventConnection
from spinn_front_end_common.utilities.constants import NOTIFY_PORT
from spinn_front_end_common.utilities.globals_variables import get_simulator

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
            local_host, local_port, simulator=get_simulator())

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
