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

import math
import socket
from threading import Thread
import numpy
from spinnman.utilities.socket_utils import (
    get_udp_socket, get_socket_address, bind_socket)

# Value of brightest pixel to show
_DISPLAY_MAX = 33.0
# How regularity to display frames
_FRAME_TIME_MS = 10
# Time constant of pixel decay
_DECAY_TIME_CONSTANT_MS = 100
_BUFFER_SIZE = 512


class PushBotRetinaViewer(Thread):
    """ A viewer for the pushbot's retina. This is a thread that can be \
        launched in parallel with the control code.

    Based on matplotlib
    """

    def __init__(
            self, resolution, port=0, display_max=_DISPLAY_MAX,
            frame_time_ms=_FRAME_TIME_MS,
            decay_time_constant_ms=_DECAY_TIME_CONSTANT_MS):
        """
        :param PushBotRetinaResolution resolution:
        :param int port:
        :param float display_max: Value of brightest pixel to show
        :param int frame_time_ms:
            How regularity to display frames (milliseconds)
        :param int decay_time_constant_ms:
            Time constant of pixel decay (milliseconds)
        """
        # pylint: disable=too-many-arguments
        try:
            from matplotlib import pyplot  # NOQA
            from matplotlib import animation  # NOQA
            self.__pyplot = pyplot
            self.__animation = animation
        except ImportError as e:
            raise Exception(
                "matplotlib must be installed to use this viewer") from e

        super().__init__(name="PushBotRetinaViewer")
        self.__display_max = display_max
        self.__frame_time_ms = frame_time_ms
        self.__image = None

        # Open socket to receive UDP
        self._init_socket(port)

        # Determine mask for coordinates
        self.__coordinate_mask = \
            (1 << (2 * resolution.bits_per_coordinate)) - 1

        # Set up the image
        self.__image_data = numpy.zeros(resolution.pixels * resolution.pixels)
        self.__image_data_view = self.__image_data.view()
        self.__image_data_view.shape = (resolution.pixels, resolution.pixels)

        # Calculate decay proportion each frame
        self.__decay_proportion = math.exp(
            -float(self.__frame_time_ms) / float(decay_time_constant_ms))

    def _init_socket(self, port):
        """ Open socket to receive UDP.
        """
        self.__spike_socket = get_udp_socket()
        bind_socket(self.__spike_socket, "0.0.0.0", port)
        self.__spike_socket.setblocking(False)

        self.__local_host, self.__local_port = get_socket_address(
            self.__spike_socket)

    @property
    def local_host(self):
        return self.__local_host

    @property
    def local_port(self):
        return self.__local_port

    def _close(self):
        self.__spike_socket.close()

    def _parse_raw_data(self, raw_data):
        # Slice off EIEIO header and timestamp, and convert to numpy
        # array of uint32
        payload = numpy.fromstring(raw_data[6:], dtype="uint32")

        # Mask out x, y coordinates
        payload &= self.__coordinate_mask

        # Increment these pixels
        self.__image_data[payload] += 1.0

    def _updatefig(self):
        # Read all UDP messages received during last frame
        while True:
            try:
                self._parse_raw_data(self.__spike_socket.recv(_BUFFER_SIZE))
            except socket.error:
                # Stop reading
                break

        # Decay image data
        self.__image_data *= self.__decay_proportion

        # Set image data
        self.__image.set_array(self.__image_data_view)
        return [self.__image]

    def run(self):
        """ How the viewer works when the thread is running.
        """
        # Create image plot of retina output
        fig = self.__pyplot.figure()
        self.__image = self.__pyplot.imshow(
            self.__image_data_view, cmap="viridis", vmin=0.0,
            vmax=self.__display_max)

        # Play animation
        self.__animation.FuncAnimation(
            fig, (lambda _frame: self._updatefig()),
            interval=self.__frame_time_ms, blit=True)
        self.__pyplot.show()
