import math
import socket
from threading import Thread
import numpy

# Value of brightest pixel to show
_DISPLAY_MAX = 33.0
# How regularity to display frames
_FRAME_TIME_MS = 10
# Time constant of pixel decay
_DECAY_TIME_CONSTANT_MS = 100


class PushBotRetinaViewer(Thread):
    def __init__(
            self, resolution, port=0, display_max=_DISPLAY_MAX,
            frame_time_ms=_FRAME_TIME_MS,
            decay_time_constant_ms=_DECAY_TIME_CONSTANT_MS):
        # pylint: disable=too-many-arguments
        try:
            from matplotlib import pyplot  # NOQA
            from matplotlib import animation  # NOQA
            self.__pyplot = pyplot
            self.__animation = animation
        except ImportError:
            raise Exception("matplotlib must be installed to use this viewer")

        super(PushBotRetinaViewer, self).__init__(name="PushBotRetinaViewer")
        self.__display_max = display_max
        self.__frame_time_ms = frame_time_ms
        self.__image = None
        self.__ani = None

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
        self.__spike_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__spike_socket.bind(("0.0.0.0", port))
        self.__spike_socket.setblocking(False)

        self.__local_host, self.__local_port = \
            self.__spike_socket.getsockname()

    @property
    def local_host(self):
        return self.__local_host

    @property
    def local_port(self):
        return self.__local_port

    def _recv_data(self, size=512):
        return self.__spike_socket.recv(size)

    def _close(self):
        self.__spike_socket.close()

    def _updatefig(self, frame):  # @UnusedVariable
        # Read all UDP messages received during last frame
        while True:
            try:
                raw_data = self._recv_data()
            except socket.error:
                # Stop reading
                break
            else:
                # Slice off eieio header and timestamp, and convert to numpy
                # array of uint32
                payload = numpy.fromstring(raw_data[6:], dtype="uint32")

                # Mask out x, y coordinates
                payload &= self.__coordinate_mask

                # Increment these pixels
                self.__image_data[payload] += 1.0

        # Decay image data
        self.__image_data *= self.__decay_proportion

        # Set image data
        self.__image.set_array(self.__image_data_view)
        return [self.__image]

    def run(self):
        # Create image plot of retina output
        fig = self.__pyplot.figure()
        self.__image = self.__pyplot.imshow(
            self.__image_data_view, cmap="jet", vmin=0.0,
            vmax=self.__display_max)

        # Play animation
        self.__ani = self.__animation.FuncAnimation(
            fig, self._updatefig, interval=self.__frame_time_ms,
            blit=True)
        self.__pyplot.show()
