import logging
from threading import RLock

import numpy

from spinnman.connections import ConnectionListener
from spynnaker.pyNN.connections import SpynnakerLiveSpikesConnection
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_parameters \
    import PushBotRetinaResolution

logger = logging.getLogger(__name__)

_RETINA_PACKET_SIZE = 2


class PushBotRetinaConnection(SpynnakerLiveSpikesConnection):
    """ A connection that sends spikes from the PushBot retina to a\
        spike injector in SpiNNaker.  Note that this assumes a packet format\
        of 16-bits per retina event.
    """

    def __init__(
            self, retina_injector_label, pushbot_wifi_connection,
            resolution=PushBotRetinaResolution.NATIVE_128_X_128,
            local_host=None, local_port=None):
        SpynnakerLiveSpikesConnection.__init__(
            self, send_labels=[retina_injector_label], local_host=local_host,
            local_port=local_port)
        self._retina_injector_label = retina_injector_label
        self._pushbot_listener = ConnectionListener(
            pushbot_wifi_connection, n_processes=1)

        self._pixel_shift = 7 - resolution.value.bits_per_coordinate
        self._x_shift = resolution.value.bits_per_coordinate
        self._y_shift = 0
        self._p_shift = resolution.value.bits_per_coordinate * 2

        self._pushbot_listener.add_callback(self._receive_retina_data)
        self._pushbot_listener.start()
        self._old_data = None
        self._lock = RLock()

    def _receive_retina_data(self, data):
        """ Receive retina packets from the pushbot and converts them into\
            neuron spikes within the spike injector system.

        :param data: Data to be processed
        """
        self._lock.acquire()

        # combine it with any leftover data from last time through the loop
        if self._old_data is not None:
            data = self._old_data + data
            self._old_data = None

        # Put the data in a numpy array
        data_all = numpy.fromstring(data, numpy.uint8).astype(numpy.uint32)
        ascii_index = numpy.where(data_all[::_RETINA_PACKET_SIZE] < 0x80)[0]
        offset = 0
        while len(ascii_index) > 0:
            index = ascii_index[0] * _RETINA_PACKET_SIZE
            stop_index = numpy.where(data_all[index:] >= 0x80)[0]
            if len(stop_index) > 0:
                stop_index = index + stop_index[0]
            else:
                stop_index = len(data)

            data_all = numpy.hstack(
                (data_all[:index], data_all[stop_index:]))
            offset += stop_index - index
            ascii_index = numpy.where(
                data_all[::_RETINA_PACKET_SIZE] < 0x80)[0]

        extra = len(data_all) % _RETINA_PACKET_SIZE
        if extra != 0:
            self._old_data = data[-extra:]
            data_all = data_all[:-extra]

        if len(data_all) > 0:

            # now process those retina events
            xs = (data_all[::_RETINA_PACKET_SIZE] & 0x7f) >> self._pixel_shift
            ys = (data_all[1::_RETINA_PACKET_SIZE] & 0x7f) >> self._pixel_shift
            polarity = numpy.where(
                data_all[1::_RETINA_PACKET_SIZE] >= 0x80, 1, 0)
            neuron_ids = (
                (xs << self._x_shift) |
                (ys << self._y_shift) |
                (polarity << self._p_shift)
            )
            self.send_spikes(self._retina_injector_label, neuron_ids)

        self._lock.release()
