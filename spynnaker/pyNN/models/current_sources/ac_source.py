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

import numpy
from typing import Dict, Mapping
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_current_source import (
    AbstractCurrentSource, CurrentSourceIDs, CurrentParameter)


class ACSource(AbstractCurrentSource):
    """
    AC current source (i.e. sine wave) turned on at "start" and off at
    "stop", given (y-)offset, amplitude, frequency and phase.
    """
    __slots__ = (
        "__start",
        "__stop",
        "__amplitude",
        "__offset",
        "__frequency",
        "__phase",
        "__parameters",
        "__parameter_types")

    def __init__(self, start=0.0, stop=0.0, amplitude=0.0, offset=0.0,
                 frequency=0.0, phase=0.0) -> None:
        """
        :param float start:
        :param float stop:
        :param float amplitude:
        :param float offset:
        :param float frequency:
        :param float phase:
        """
        # There's probably no need to actually store these as you can't
        # access them directly in pynn anyway
        time_convert_ms = SpynnakerDataView.get_simulation_time_step_per_ms()
        self.__start = int(start * time_convert_ms)
        self.__stop = int(stop * time_convert_ms)
        self.__amplitude = amplitude
        self.__offset = offset
        self.__frequency = self._get_frequency(frequency)
        self.__phase = self._get_phase(phase)

        self.__parameter_types = {
            'start': DataType.UINT32,
            'stop': DataType.UINT32,
            'amplitude': DataType.S1615,
            'offset': DataType.S1615,
            'frequency': DataType.S1615,
            'phase': DataType.S1615}

        self.__parameters: Dict[str, CurrentParameter] = {
            'start': self.__start,
            'stop': self.__stop,
            'amplitude': self.__amplitude,
            'offset': self.__offset,
            'frequency': self.__frequency,
            'phase': self.__phase}

        super().__init__()

    @overrides(AbstractCurrentSource.set_parameters)
    def set_parameters(self, **parameters: CurrentParameter):
        for key, value in parameters.items():
            if key not in self.__parameters.keys():
                # throw an exception
                raise SpynnakerException(f"{key} is not a parameter of {self}")
            if key == 'frequency':
                self.__parameters[key] = self._get_frequency(value)
            elif key == 'phase':
                self.__parameters[key] = self._get_phase(value)
            else:
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
        return CurrentSourceIDs.AC_SOURCE.value

    @overrides(AbstractCurrentSource.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self) -> int:
        return len(self.__parameters) * BYTES_PER_WORD

    def _get_frequency(self, frequency: CurrentParameter) -> float:
        """
        Convert frequency to radian-friendly value.

        :rtype: float
        """
        if not isinstance(frequency, (int, float)):
            raise TypeError
        # convert frequency and phase into radians, remembering that
        # frequency is given in Hz but we are using ms for timesteps
        return (frequency * 2 * numpy.pi) / 1000.0

    def _get_phase(self, phase: CurrentParameter) -> float:
        """
        Convert phase to radian-friendly value.

        :rtype: float
        """
        if not isinstance(phase, (int, float)):
            raise TypeError
        return phase * (numpy.pi / 180.0)
