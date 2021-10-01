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

from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, MICRO_TO_MILLISECOND_CONVERSION)
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_current_source import AbstractCurrentSource, CurrentSourceIDs


class DCSource(AbstractCurrentSource):
    """ Current source with amplitude turned on at "start" and off at "stop"

    """
    __slots__ = [
        "__amplitude",
        "__start",
        "__stop",
        "__parameters",
        "__parameter_types",
        "__app_vertex"]

    def __init__(self, amplitude=0.0, start=0.0, stop=0.0):
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
        sim = get_simulator()
        machine_ts = sim.machine_time_step
        time_convert_ms = MICRO_TO_MILLISECOND_CONVERSION / machine_ts
        self.__parameters['start'] = self.__start * time_convert_ms
        self.__parameters['stop'] = self.__stop * time_convert_ms

        self.__app_vertex = None

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
                self.__parameters[key] = value

        # Parameters have been set, so if multi-run then it will have been
        # injected already; if not then it can just be ignored
        if self.__app_vertex is not None:
            for m_vertex in self.__app_vertex.machine_vertices:
                m_vertex.set_reload_required(True)

    @overrides(AbstractCurrentSource.set_app_vertex)
    def set_app_vertex(self, vertex):
        self.__app_vertex = vertex

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
        return CurrentSourceIDs.DC_SOURCE.value

    @overrides(AbstractCurrentSource.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self):
        """ The sdram usage of the current source.

        :rtype: int
        """
        return len(self.__parameters) * BYTES_PER_WORD
