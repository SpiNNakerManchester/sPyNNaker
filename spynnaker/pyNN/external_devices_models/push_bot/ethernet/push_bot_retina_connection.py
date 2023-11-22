# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from threading import RLock
import numpy
from spinnman.connections import ConnectionListener
from spinn_front_end_common.utilities.constants import BYTES_PER_SHORT
from spynnaker.pyNN.connections import SpynnakerLiveSpikesConnection
from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotRetinaResolution)

# Each value is a 16-bit 1yyyyyyy.pxxxxxxx
_RETINA_PACKET_SIZE = BYTES_PER_SHORT
_MIN_PIXEL_VALUE = 32768
_BITS_PER_PIXEL = 7
_Y_SHIFT = 0
_X_SHIFT = 8
_P_SHIFT = 7
_P_MASK = 0x1


class PushBotRetinaConnection(SpynnakerLiveSpikesConnection):
    """
    A connection that sends spikes from the PushBot retina to a spike injector
    in SpiNNaker.

    .. note::
        This assumes a packet format of 16-bits per retina event.
    """
    __slots__ = (
        "__lock",
        "__p_shift",
        "__pixel_shift",
        "__pushbot_listener",
        "__retina_injector_label",
        "__x_shift",
        "__y_shift",
        "__orig_x_shift",
        "__orig_y_shift",
        "__x_mask",
        "__y_mask",
        "__next_data",
        "__ready")

    def __init__(
            self, retina_injector_label, pushbot_wifi_connection,
            resolution=PushBotRetinaResolution.NATIVE_128_X_128,
            local_host=None, local_port=None):
        """
        :param str retina_injector_label:
        :param PushBotWIFIConnection pushbot_wifi_connection:
        :param PushBotRetinaResolution resolution:
        :param local_host:
        :type local_host: str or None
        :param local_port:
        :type local_port: int or None
        """
        # pylint: disable=too-many-arguments
        super().__init__(
            send_labels=[retina_injector_label], local_host=local_host,
            local_port=local_port)
        self.__retina_injector_label = retina_injector_label
        self.__pushbot_listener = ConnectionListener(
            pushbot_wifi_connection, n_processes=1)

        add_shift = _BITS_PER_PIXEL - resolution.value.bits_per_coordinate
        mask = (2 ** resolution.value.bits_per_coordinate) - 1
        self.__y_shift = resolution.value.bits_per_coordinate
        self.__orig_x_shift = add_shift + _X_SHIFT
        self.__x_mask = mask
        self.__x_shift = 0
        self.__orig_y_shift = add_shift + _Y_SHIFT
        self.__y_mask = mask
        self.__p_shift = resolution.value.bits_per_coordinate * 2

        self.__pushbot_listener.add_callback(self._receive_retina_data)
        self.__pushbot_listener.start()
        self.__lock = RLock()

        self.__next_data = None
        self.__ready = False

        self.add_start_resume_callback(
            retina_injector_label, self.__push_bot_start)
        self.add_pause_stop_callback(
            retina_injector_label, self.__push_bot_stop)

    # pylint: disable=unused-argument
    def __push_bot_start(self, label, connection):
        with self.__lock:
            self.__ready = True

    # pylint: disable=unused-argument
    def __push_bot_stop(self, label, connection):
        with self.__lock:
            self.__ready = False

    def _receive_retina_data(self, data):
        """
        Receive retina packets from the PushBot and converts them into
        neuron spikes within the spike injector system.

        :param bytearray data: Data to be processed
        """
        with self.__lock:
            if not self.__ready:
                return

            if self.__next_data is not None:
                data = data + self.__next_data
                self.__next_data = None

            # Go through the data and find pairs where the first of the pair
            # has a 1 in the MSB
            data_all = b''
            for i in range(len(data)):
                if data[i] > 128:
                    if i + 1 < len(data):
                        data_all += data[i:i+2]
                        i += 1
                    else:
                        self.__next_data = data[i:i+1]

            # Filter out the usable data
            data_filtered = numpy.fromstring(data_all, dtype=numpy.uint16)
            y_values = (data_filtered >> self.__orig_y_shift) & self.__y_mask
            x_values = (data_filtered >> self.__orig_x_shift) & self.__x_mask
            polarity = (data_filtered >> _P_SHIFT) & _P_MASK
            neuron_ids = (
                (x_values << self.__x_shift) |
                (y_values << self.__y_shift) |
                (polarity << self.__p_shift))
            self.send_spikes(self.__retina_injector_label, neuron_ids)
