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
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_current_source import AbstractCurrentSource, CurrentSourceIDs


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
                 frequency=0.0, phase=0.0):
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
        self.__start = start * time_convert_ms
        self.__stop = stop * time_convert_ms
        self.__amplitude = amplitude
        self.__offset = offset
        self.__frequency = self._get_frequency(frequency)
        self.__phase = self._get_phase(phase)

        self.__parameter_types = dict()
        self.__parameter_types['start'] = DataType.UINT32
        self.__parameter_types['stop'] = DataType.UINT32
        self.__parameter_types['amplitude'] = DataType.S1615
        self.__parameter_types['offset'] = DataType.S1615
        self.__parameter_types['frequency'] = DataType.S1615
        self.__parameter_types['phase'] = DataType.S1615

        self.__parameters = dict()
        self.__parameters['start'] = self.__start
        self.__parameters['stop'] = self.__stop
        self.__parameters['amplitude'] = self.__amplitude
        self.__parameters['offset'] = self.__offset
        self.__parameters['frequency'] = self.__frequency
        self.__parameters['phase'] = self.__phase

        super().__init__()

    @overrides(AbstractCurrentSource.set_parameters)
    def set_parameters(self, **parameters):
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
    @overrides(AbstractCurrentSource.get_parameters)
    def get_parameters(self):
        return self.__parameters

    @property
    @overrides(AbstractCurrentSource.get_parameter_types)
    def get_parameter_types(self):
        return self.__parameter_types

    @property
    @overrides(AbstractCurrentSource.current_source_id)
    def current_source_id(self):
        return CurrentSourceIDs.AC_SOURCE.value

    @overrides(AbstractCurrentSource.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self):
        return len(self.__parameters) * BYTES_PER_WORD

    def _get_frequency(self, frequency):
        """
        Convert frequency to radian-friendly value.

        :rtype: float
        """
        # convert frequency and phase into radians, remembering that
        # frequency is given in Hz but we are using ms for timesteps
        return (frequency * 2 * numpy.pi) / 1000.0

    def _get_phase(self, phase):
        """
        Convert phase to radian-friendly value.

        :rtype: float
        """
        return phase * (numpy.pi / 180.0)
