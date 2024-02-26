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

from typing import Dict, Mapping
import numpy

from spinn_utilities.overrides import overrides

from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.utilities import utility_calls

from .abstract_current_source import (
    AbstractCurrentSource, CurrentSourceIDs, CurrentParameter)


class NoisyCurrentSource(AbstractCurrentSource):
    """
    A noisy current source beginning at "start" and ending at "stop", with
    noise simulated based on the given mean and standard deviation, and
    updating every `dt` (`dt` should default to the machine time step).
    """
    __slots__ = (
        "__mean",
        "__stdev",
        "__start",
        "__stop",
        "__dt",
        "__rng",
        "__parameters",
        "__parameter_types")

    def __init__(self, mean=0.0, stdev=0.0, start=0.0, stop=0.0, dt=1.0,
                 rng=None) -> None:
        """
        :param float mean:
        :param float stdev:
        :param float start:
        :param float stop:
        :param float dt:
        :param rng:
        """
        # There's probably no need to actually store these as you can't
        # access them directly in pynn anyway
        time_convert_ms = SpynnakerDataView.get_simulation_time_step_per_ms()
        self.__mean = mean
        self.__stdev = stdev
        self.__start = int(start * time_convert_ms)
        self.__stop = int(stop * time_convert_ms)
        self.__dt = dt * time_convert_ms
        if rng is None:
            seed = None
            self.__rng = numpy.random.RandomState(seed)
        # TODO: What happens if we pass a non-None rng?

        # Error if dt is not the same as machine time step
        if dt != (1 / time_convert_ms):
            raise SpynnakerException(
                "Only currently supported for dt = machine_time_step, here "
                f"dt = {dt} and machine_time_step = {1 / time_convert_ms}")

        self.__parameter_types = {
            'mean': DataType.S1615,
            'stdev': DataType.S1615,
            'start': DataType.UINT32,
            'stop': DataType.UINT32,
            'dt': DataType.S1615,
            'seed': DataType.UINT32}

        self.__parameters: Dict[str, CurrentParameter] = {
            'mean': self.__mean,
            'stdev': self.__stdev,
            'start': self.__start,
            'stop': self.__stop,
            'dt': self.__dt,
            'seed': utility_calls.create_mars_kiss_seeds(self.__rng)}

        super().__init__()

    @overrides(AbstractCurrentSource.set_parameters)
    def set_parameters(self, **parameters: CurrentParameter):
        for key, value in parameters.items():
            if key not in self.__parameters.keys():
                # throw an exception
                raise SpynnakerException(f"{key} is not a parameter of {self}")
            self.__parameters[key] = value

        # Parameters have been set, so if multi-run then it will have been
        # injected already; if not then it can just be ignored
        if self.app_vertex is not None:
            for m_vertex in self.app_vertex.machine_vertices:
                m_vertex.set_reload_required(True)

    @property
    @overrides(AbstractCurrentSource.parameters)
    def parameters(self) -> Mapping[str, CurrentParameter]:
        return self.__parameters

    @property
    @overrides(AbstractCurrentSource.parameter_types)
    def parameter_types(self) -> Mapping[str, DataType]:
        return self.__parameter_types

    @property
    @overrides(AbstractCurrentSource.current_source_id)
    def current_source_id(self) -> int:
        return CurrentSourceIDs.NOISY_CURRENT_SOURCE.value

    @overrides(AbstractCurrentSource.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self) -> int:
        # 3 because the seed parameter has length 4
        return (len(self.__parameters) + 3) * BYTES_PER_WORD
