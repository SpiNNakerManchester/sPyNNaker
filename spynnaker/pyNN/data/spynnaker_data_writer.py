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

import logging
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_front_end_common.data.fec_data_writer import FecDataWriter
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from .spynnaker_data_view import SpynnakerDataView, _SpynnakerDataModel

logger = FormatAdapter(logging.getLogger(__name__))


class SpynnakerDataWriter(FecDataWriter, SpynnakerDataView):
    """
    Writer class for the Spy Data building one the Fec writer

    """

    __spy_data = _SpynnakerDataModel()

    @overrides(FecDataWriter.setup)
    def setup(self):
        FecDataWriter.setup(self)
        self.__spy_data._clear()

    @overrides(FecDataWriter.mock)
    def mock(self):
        FecDataWriter.mock(self)
        self._set_min_delay(1)

    def set_up_timings_and_delay(
            self, simulation_time_step_us, time_scale_factor, min_delay):
        try:
            self.set_up_timings(simulation_time_step_us, time_scale_factor)
            self._set_min_delay(min_delay)
        except ConfigurationException:
            self.__spy_data._min_delay = None
            raise

    def _set_min_delay(self, min_delay):
        """
        Sets a min delay or accepts None to use simulation_time_step_ms

        :param min_delay: new value or None to say use simulation_time_step_ms
        :type min_delay: int, float or None
        """
        if min_delay is None:
            min_delay = self.simulation_time_step_ms

        if not isinstance(min_delay, (int, float)):
            raise TypeError("min_delay should be an float (or int)")

        if min_delay < self.simulation_time_step_ms:
            raise ConfigurationException(
                f'invalid min_delay: {min_delay} '
                f'must at least simulation time step in microseconds: '
                f'{self.get_simulation_time_step_ms()}')

        raw = min_delay / self.get_simulation_time_step_ms()
        rounded = round(raw)
        if abs(rounded - raw) > 0.00001:
            raise ConfigurationException(
                f'invalid min_delay {min_delay} '
                f'must at multiple of simulation time step in microseconds '
                f' {self.get_simulation_time_step_ms()}')

        self.__spy_data._min_delay = min_delay
