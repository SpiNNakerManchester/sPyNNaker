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

from typing import Dict, Mapping, Sequence
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import DataType
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_current_source import (
    AbstractCurrentSource, CurrentSourceIDs, CurrentParameter)


class StepCurrentSource(AbstractCurrentSource):
    """
    Current source where the amplitude changes based on a time array.
    """
    __slots__ = (
        "__amplitudes",
        "__times",
        "__parameters",
        "__parameter_types")

    def __init__(
            self, times: Sequence[int] = (), amplitudes: Sequence[float] = ()):
        """
        :param list(int) times:
        :param list(float) amplitudes:
        """
        # There's probably no need to actually store these as you can't
        # access them directly in pynn anyway
        time_convert_ms = SpynnakerDataView.get_simulation_time_step_per_ms()
        self.__times = [
            int(times[i] * time_convert_ms) for i in range(len(times))]
        self.__amplitudes = amplitudes

        if len(times) != len(amplitudes):
            raise SpynnakerException(
                f"In StepCurrentSource, len(times) is {len(times)}, "
                f" but len(amplitudes) is {len(amplitudes)}")

        self.__parameter_types = {
            'times': DataType.UINT32,  # arrays?
            'amplitudes': DataType.S1615}

        self.__parameters: Dict[str, CurrentParameter] = {
            'times': self.__times,
            'amplitudes': self.__amplitudes}

        super().__init__()

    @overrides(AbstractCurrentSource.set_parameters)
    def set_parameters(self, **parameters: CurrentParameter):
        for key, value in parameters.items():
            if key not in self.__parameters.keys():
                # throw an exception
                raise SpynnakerException(f"{key} is not a parameter of {self}")
            if not isinstance(value, Sequence):
                raise TypeError
            if key == 'times':
                time_convert_ms = SpynnakerDataView.\
                    get_simulation_time_step_per_ms()
                self.__times = [
                    int(value[i] * time_convert_ms) for i in range(len(value))]
                value = self.__times
            else:
                # Check length: if longer, need to remap
                if len(self.__amplitudes) < len(value):
                    if self.population is not None:
                        SpynnakerDataView.set_requires_mapping()

                self.__amplitudes = value
            self.__parameters[key] = value

        # Check the arrays are still the same lengths
        if len(self.__times) != len(self.__amplitudes):
            raise SpynnakerException(
                f"In StepCurrentSource, len(times) is {len(self.__times)}, "
                f"but len(amplitudes) is {len(self.__amplitudes)}")

        # Parameters have been set, so if multi-run then it will have been
        # injected already; if not then it can just be ignored
        if self.app_vertex is not None:
            for m_vertex in self.app_vertex.machine_vertices:
                m_vertex.set_reload_required(True)

    @property
    @overrides(AbstractCurrentSource.get_parameters)
    def get_parameters(self) -> Mapping[str, CurrentParameter]:
        return self.__parameters

    @property
    @overrides(AbstractCurrentSource.get_parameter_types)
    def get_parameter_types(self) -> Mapping[str, DataType]:
        return self.__parameter_types

    @property
    @overrides(AbstractCurrentSource.current_source_id)
    def current_source_id(self) -> int:
        return CurrentSourceIDs.STEP_CURRENT_SOURCE.value

    @overrides(AbstractCurrentSource.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self) -> int:
        # The parameters themselves take up this amount of space
        # ((len(times) + length_val)) * 2) + ID
        sdram_for_parameters = ((len(self.__times) + 1) * 2) * BYTES_PER_WORD

        # For each_source there is the last amplitude holder and index
        sdram_for_on_core_calcs = 2 * BYTES_PER_WORD

        return sdram_for_parameters + sdram_for_on_core_calcs
        # return sdram_for_parameters
