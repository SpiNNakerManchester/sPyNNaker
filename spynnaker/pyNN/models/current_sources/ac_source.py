# Copyright (c) 2017-2021 The University of Manchester
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

import numpy
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, MICRO_TO_MILLISECOND_CONVERSION)
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_current_source import AbstractCurrentSource, CurrentSourceIDs


class ACSource(AbstractCurrentSource):
    """ AC current source (i.e. sine wave) turned on at "start" and off at
        "stop", given (y-)offset, amplitude, frequency and phase

    """
    __slots__ = [
        "__start",
        "__stop",
        "__amplitude",
        "__offset",
        "__frequency",
        "__phase",
        "__parameters",
        "__parameter_types"]

    def __init__(self, start=0.0, stop=0.0, amplitude=0.0, offset=0.0,
                 frequency=0.0, phase=0.0):
        # There's probably no need to actually store these as you can't
        # access them directly in pynn anyway
        sim = get_simulator()
        machine_ts = sim.machine_time_step
        time_convert_ms = MICRO_TO_MILLISECOND_CONVERSION / machine_ts
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

    def set_parameters(self, **parameters):
        """ Set the current source parameters

        :param parameters: the parameters to set
        """
        for key, value in parameters.items():
            if key not in self.__parameters.keys():
                # throw an exception
                msg = "{} is not a parameter of {}".format(key, self)
                raise SpynnakerException(msg)
            else:
                if key == 'frequency':
                    self.__parameters[key] = self._get_frequency(value)
                elif key == 'phase':
                    self.__parameters[key] = self._get_phase(value)
                else:
                    self.__parameters[key] = value

    @property
    @overrides(AbstractCurrentSource.get_parameters)
    def get_parameters(self):
        """ Get the parameters of the current source

        :rtype dict(str, Any)
        """
        return self.__parameters

    @property
    @overrides(AbstractCurrentSource.get_parameter_types)
    def get_parameter_types(self):
        """ Get the parameters of the current source

        :rtype dict(str, Any)
        """
        return self.__parameter_types

    @property
    @overrides(AbstractCurrentSource.current_source_id)
    def current_source_id(self):
        """ The ID of the current source.

        :rtype: int
        """
        return CurrentSourceIDs.AC_SOURCE.value

    @overrides(AbstractCurrentSource.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self):
        """ The sdram usage of the current source.

        :rtype: int
        """
        return len(self.__parameters) * BYTES_PER_WORD

    def _get_frequency(self, frequency):
        """ Convert frequency to radian-friendly value.

        :rtype: float
        """
        # convert frequency and phase into radians, remembering that
        # frequency is given in Hz but we are using ms for timesteps
        return (frequency * 2 * numpy.pi) / 1000.0

    def _get_phase(self, phase):
        """ Convert phase to radian-friendly value.

        :rtype: float
        """
        return phase * (numpy.pi / 180.0)
