import logging
from threading import RLock
import numpy
from spinnman.connections import ConnectionListener
from spynnaker.pyNN.connections import SpynnakerLiveSpikesConnection
from spynnaker.pyNN.external_devices_models.push_bot.push_bot_parameters \
    import (
        PushBotRetinaResolution)

logger = logging.getLogger(__name__)
_RETINA_PACKET_SIZE = 2


class PushBotRetinaConnection(SpynnakerLiveSpikesConnection):
    """ A connection that sends spikes from the PushBot retina to a\
        spike injector in SpiNNaker.  Note that this assumes a packet format\
        of 16-bits per retina event.
    """
    __slots__ = [
        "__lock",
        "__old_data",
        "__p_shift",
        "__pixel_shift",
        "__pushbot_listener",
        "__retina_injector_label",
        "__x_shift",
        "__y_shift"]

    def __init__(
            self, retina_injector_label, pushbot_wifi_connection,
            resolution=PushBotRetinaResolution.NATIVE_128_X_128,
            local_host=None, local_port=None):
        # pylint: disable=too-many-arguments
        super(PushBotRetinaConnection, self).__init__(
            send_labels=[retina_injector_label], local_host=local_host,
            local_port=local_port)
        self.__retina_injector_label = retina_injector_label
        self.__pushbot_listener = ConnectionListener(
            pushbot_wifi_connection, n_processes=1)

        self.__pixel_shift = 7 - resolution.value.bits_per_coordinate
        self.__x_shift = resolution.value.bits_per_coordinate
        self.__y_shift = 0
        self.__p_shift = resolution.value.bits_per_coordinate * 2

        self.__pushbot_listener.add_callback(self._receive_retina_data)
        self.__pushbot_listener.start()
        self.__old_data = None
        self.__lock = RLock()

    def _receive_retina_data(self, data):
        """ Receive retina packets from the PushBot and converts them into\
            neuron spikes within the spike injector system.

        :param data: Data to be processed
        """
        with self.__lock:
            # combine it with any leftover data from last time through the loop
            if self.__old_data is not None:
                data = self.__old_data + data
                self.__old_data = None

            # Put the data in a numpy array
            data_all = numpy.fromstring(data, numpy.uint8).astype(numpy.uint32)
            ascii_index = numpy.where(
                data_all[::_RETINA_PACKET_SIZE] < 0x80)[0]
            offset = 0
            while ascii_index.size:
                index = ascii_index[0] * _RETINA_PACKET_SIZE
                stop_index = numpy.where(data_all[index:] >= 0x80)[0]
                if stop_index.size:
                    stop_index = index + stop_index[0]
                else:
                    stop_index = len(data)

                data_all = numpy.hstack(
                    (data_all[:index], data_all[stop_index:]))
                offset += stop_index - index
                ascii_index = numpy.where(
                    data_all[::_RETINA_PACKET_SIZE] < 0x80)[0]

            extra = data_all.size % _RETINA_PACKET_SIZE
            if extra:
                self.__old_data = data[-extra:]
                data_all = data_all[:-extra]

            if data_all.size:
                # now process those retina events
                xs = (data_all[::_RETINA_PACKET_SIZE] & 0x7f) \
                    >> self.__pixel_shift
                ys = (data_all[1::_RETINA_PACKET_SIZE] & 0x7f) \
                    >> self.__pixel_shift
                polarity = numpy.where(
                    data_all[1::_RETINA_PACKET_SIZE] >= 0x80, 1, 0)
                neuron_ids = (
                    (xs << self.__x_shift) |
                    (ys << self.__y_shift) |
                    (polarity << self.__p_shift))
                self.send_spikes(self.__retina_injector_label, neuron_ids)
