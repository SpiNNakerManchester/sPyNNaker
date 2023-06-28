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

from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_current_source import AbstractCurrentSource, CurrentSourceIDs


class DCSource(AbstractCurrentSource):
    """
    Current source with amplitude turned on at "start" and off at "stop".
    """
    __slots__ = (
        "__amplitude",
        "__start",
        "__stop",
        "__parameters",
        "__parameter_types")

    def __init__(self, amplitude=0.0, start=0.0, stop=0.0):
        """
        :param float amplitude:
        :param float start:
        :param float stop:
        """
        # There's probably no need to actually store these as you can't
        # access them directly in pynn anyway
        self.__amplitude = amplitude
        self.__start = start
        self.__stop = stop

        self.__parameter_types = dict()
        self.__parameter_types['amplitude'] = DataType.S1615
        # Anything associated with timing needs to be an integer on the machine
        self.__parameter_types['start'] = DataType.UINT32
        self.__parameter_types['stop'] = DataType.UINT32

        self.__parameters = dict()
        self.__parameters['amplitude'] = self.__amplitude
        # Convert to integers i.e. timesteps
        time_convert_ms = SpynnakerDataView.get_simulation_time_step_per_ms()
        self.__parameters['start'] = self.__start * time_convert_ms
        self.__parameters['stop'] = self.__stop * time_convert_ms

        super().__init__()

    @overrides(AbstractCurrentSource.set_parameters)
    def set_parameters(self, **parameters):
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
        return CurrentSourceIDs.DC_SOURCE.value

    @overrides(AbstractCurrentSource.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self):
        return len(self.__parameters) * BYTES_PER_WORD
