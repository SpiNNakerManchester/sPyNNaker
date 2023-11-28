# Copyright (c) 2021 The University of Manchester
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
from typing import Optional, Union
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_front_end_common.data.fec_data_writer import FecDataWriter
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from .spynnaker_data_view import SpynnakerDataView, _SpynnakerDataModel

logger = FormatAdapter(logging.getLogger(__name__))
# pylint: disable=protected-access


class SpynnakerDataWriter(FecDataWriter, SpynnakerDataView):
    """
    See :py:class:`~spinn_utilities.data.utils_data_writer.UtilsDataWriter`.

    This class is designed to only be used directly by
    :py:class:`spinn_front_end_common.interface.abstract_spinnaker_base.AbstractSpinnakerBase`
    and its subclasses and within the PyNN repositories unit tests.
    """

    __spy_data = _SpynnakerDataModel()

    @overrides(FecDataWriter._setup)
    def _setup(self) -> None:
        FecDataWriter._setup(self)
        self.__spy_data._clear()

    @overrides(FecDataWriter._mock)
    def _mock(self) -> None:
        FecDataWriter._mock(self)
        self._set_min_delay(1)

    @overrides(FecDataWriter._hard_reset)
    def _hard_reset(self) -> None:
        if not self.is_soft_reset():
            # Only increase it if this is a hard not following a soft
            self.__spy_data._segment_counter += 1
        FecDataWriter._hard_reset(self)
        self.__spy_data._hard_reset()

    @overrides(FecDataWriter._soft_reset)
    def _soft_reset(self) -> None:
        self.__spy_data._segment_counter += 1
        FecDataWriter._soft_reset(self)
        self.__spy_data._soft_reset()

    def set_up_timings_and_delay(
            self, simulation_time_step_us: Optional[int],
            time_scale_factor: Optional[float],
            min_delay: Optional[Union[int, float]]):
        """
        :param simulation_time_step_us:
            An explicitly specified time step for the simulation in
            microseconds.
            If `None`, the value is read from the configuration
        :type simulation_time_step_us: int or None
        :param time_scale_factor:
            An explicitly specified time scale factor for the simulation.
            If `None`, the value is read from the configuration
        :type time_scale_factor: float or None
        :param min_delay:
            new value or `None` to say use simulation_time_step_ms
        :type min_delay: int, float or None
        """
        try:
            self.set_up_timings(simulation_time_step_us, time_scale_factor)
            self._set_min_delay(min_delay)
        except ConfigurationException:
            self.__spy_data._min_delay = None
            raise

    def _set_min_delay(self, min_delay: Optional[Union[int, float]]):
        """
        Sets a min delay or accepts `None` to use simulation_time_step_ms.

        :param min_delay:
            new value or `None` to say use simulation_time_step_ms
        :type min_delay: int, float or None
        """
        if min_delay is None:
            min_delay = self.get_simulation_time_step_ms()

        if not isinstance(min_delay, (int, float)):
            raise TypeError("min_delay should be an float (or int)")

        if min_delay < self.get_simulation_time_step_ms():
            raise ConfigurationException(
                f'invalid min_delay: {min_delay} '
                f'must at least simulation time step in microseconds: '
                f'{self.get_simulation_time_step_ms()}')

        raw = min_delay / self.get_simulation_time_step_ms()
        rounded = round(raw)
        if abs(rounded - raw) > 0.00001:
            raise ConfigurationException(
                f'invalid min_delay {min_delay} '
                f'must be a multiple of simulation time step in microseconds '
                f'{self.get_simulation_time_step_ms()}')

        self.__spy_data._min_delay = min_delay

    def shut_down(self) -> None:
        FecDataWriter.shut_down(self)
        # Clears all previously added ceiling on the number of neurons per core
        for neuron_type in self.__spy_data._neurons_per_core_set:
            neuron_type.set_model_max_atoms_per_dimension_per_core()
