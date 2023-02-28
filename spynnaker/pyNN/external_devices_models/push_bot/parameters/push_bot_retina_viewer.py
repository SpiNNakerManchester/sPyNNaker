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
from threading import Thread
from time import sleep
from matplotlib import pyplot
import numpy
import pyNN.spiNNaker as p

MAX_VALUE = 33.0
ADD_VALUE = 1.0
DECAY_FACTOR = 0.5
SLEEP_TIME = 0.1


class PushBotRetinaViewer():
    """ Viewer of retina from the PushBot
    """

    def __init__(self, retina_resolution, label):

        pyplot.ion()
        self.__image_data = numpy.zeros(
            (retina_resolution.value.pixels, retina_resolution.value.pixels),
            dtype=numpy.float32)
        self.__fig, axes = pyplot.subplots(figsize=(8, 8))
        self.__plot = axes.imshow(
            self.__image_data, interpolation="nearest", cmap="Greens",
            vmin=0, vmax=MAX_VALUE)
        self.__fig.canvas.draw()
        self.__fig.canvas.flush_events()

        self.__without_polarity_mask = (
            2 ** (retina_resolution.value.bits_per_coordinate * 2)) - 1
        self.__height = retina_resolution.value.pixels

        self.__running = True

        self.__conn = p.external_devices.SpynnakerLiveSpikesConnection(
            receive_labels=[label], local_port=None)
        self.__conn.add_receive_callback(label, self.__recv)

    @property
    def port(self):
        """ The port the connection is listening on

        :rtype: int
        """
        return self.__conn.local_port

    # pylint: disable=unused-argument
    def __recv(self, label, time, spikes):
        np_spikes = numpy.array(spikes) & self.__without_polarity_mask
        x_vals, y_vals = numpy.divmod(np_spikes, self.__height)
        self.__image_data[x_vals, y_vals] += 1.0

    def __run_sim_forever(self):
        p.external_devices.run_forever()
        self.__running = False
        p.end()

    def __run_sim(self, run_time):
        p.run(run_time)
        self.__running = False
        p.end()

    def __run(self, run_thread):

        while self.__running and self.__fig.get_visible():
            try:
                self.__plot.set_array(self.__image_data)
                self.__fig.canvas.draw()
                self.__fig.canvas.flush_events()
                self.__image_data *= DECAY_FACTOR
                sleep(0.1)
            # pylint: disable=broad-except
            except Exception:
                break

    def run_until_closed(self):
        """ Run the viewer and simulation until the viewer is closed.
        """
        run_thread = Thread(target=self.__run_sim_forever)
        run_thread.start()
        self.__run(run_thread)
        p.external_devices.request_stop()
        run_thread.join()

    def run(self, run_time):
        """ Run the viewer and simulation for a fixed time.
        """
        run_thread = Thread(target=self.__run_sim, args=[run_time])
        run_thread.start()
        self.__run(run_thread)
        run_thread.join()
