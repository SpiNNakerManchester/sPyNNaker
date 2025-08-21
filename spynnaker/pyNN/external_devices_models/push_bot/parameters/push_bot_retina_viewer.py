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
import logging
from threading import Thread, RLock
from time import sleep
from typing import Any, List

from matplotlib import pyplot
import numpy

from spinn_utilities.log import FormatAdapter

import spynnaker.pyNN.external_devices as external_devices
from spynnaker.pyNN.external_devices_models.push_bot.parameters import (
    PushBotRetinaResolution)
from spynnaker.pyNN.connections import SpynnakerLiveSpikesConnection

_logger = FormatAdapter(logging.getLogger(__name__))
MAX_VALUE = 33.0
ADD_VALUE = 1.0
DECAY_FACTOR = 0.5
SLEEP_TIME = 0.1


class PushBotRetinaViewer():
    """
    Viewer of retina from the PushBot.
    """
    __slots__ = (
        "__image_data", "__image_lock",
        "__without_polarity_mask", "__height",
        "__fig", "__plot",
        "__running", "__conn")

    def __init__(self, retina_resolution: PushBotRetinaResolution,
                 label: str, sim: None = None):
        # pylint: disable=wrong-spelling-in-docstring
        """
        :param retina_resolution: Size of the retina to use
        :param label:
            Label for connection over which live spikes will be received.
        :param sim: Deprecated! Do not use.
        """
        if sim is not None:
            _logger.warning("PushBotRetinaViewer: sim=None is deprecated")
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
        self.__image_lock = RLock()

        self.__conn = SpynnakerLiveSpikesConnection(
            receive_labels=[label], local_port=None)
        self.__conn.add_receive_callback(label, self.__recv)

    @property
    def port(self) -> int:
        """
        The port the connection is listening on.
        """
        return self.__conn.local_port

    def __recv(self, label: str, time: int, spikes: List[int]) -> None:
        _ = (label, time)
        np_spikes = numpy.array(spikes) & self.__without_polarity_mask
        x_vals, y_vals = numpy.divmod(np_spikes, self.__height)
        self.__image_lock.acquire()
        self.__image_data[x_vals, y_vals] += 1.0
        self.__image_lock.release()

    def __run_sim_forever(self) -> None:
        # UGLY but needed to avoid circular import
        # pylint: disable=import-outside-toplevel
        from pyNN.spiNNaker import end
        try:
            external_devices.run_forever()
            self.__running = False
            end()
        except KeyboardInterrupt:
            pass
        except Exception:  # pylint: disable=broad-except
            _logger.exception("unexpected exception in simulation thread")

    def __run_sim(self, run_time: float) -> None:
        # UGLY but needed to avoid circular import
        # pylint: disable=import-outside-toplevel
        from pyNN.spiNNaker import end, run
        try:
            run(run_time)
            self.__running = False
            end()
        except KeyboardInterrupt:
            pass
        except Exception:  # pylint: disable=broad-except
            _logger.exception("unexpected exception in simulation thread")

    def __run(self) -> None:
        try:
            while self.__running and self.__fig.get_visible():
                self.__image_lock.acquire()
                self.__plot.set_array(self.__image_data)
                self.__fig.canvas.draw()
                self.__fig.canvas.flush_events()
                self.__image_data *= DECAY_FACTOR
                self.__image_lock.release()
                sleep(0.1)
        except KeyboardInterrupt:
            pass
        except Exception:  # pylint: disable=broad-except
            _logger.exception("unexpected exception in drawing thread")

    def __on_close(self, event: Any) -> None:
        _ = event
        self.__running = False

    def run_until_closed(self) -> None:
        """
        Run the viewer and simulation until the viewer is closed.
        """
        run_thread = Thread(target=self.__run_sim_forever)
        run_thread.start()
        try:
            self.__fig.canvas.mpl_connect('close_event', self.__on_close)
            self.__run()
        finally:
            external_devices.request_stop()
            run_thread.join()

    def run(self, run_time: float) -> None:
        """
        Run the viewer and simulation for a fixed time.
        """
        run_thread = Thread(target=self.__run_sim, args=[run_time])
        run_thread.start()
        try:
            self.__run()
        finally:
            run_thread.join()
