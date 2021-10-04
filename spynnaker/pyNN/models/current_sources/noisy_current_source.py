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
from spynnaker.pyNN.utilities import utility_calls
from .abstract_current_source import AbstractCurrentSource, CurrentSourceIDs


class NoisyCurrentSource(AbstractCurrentSource):
    """ A noisy current source beginning at "start" and ending at "stop", with
        noise simulated based on the given mean and stdev, and updating every
        dt (dt should default to the machine time step)

    """
    __slots__ = [
        "__mean",
        "__stdev",
        "__start",
        "__stop",
        "__dt",
        "__rng",
        "__parameters",
        "__parameter_types"]

    def __init__(self, mean=0.0, stdev=0.0, start=0.0, stop=0.0, dt=1.0,
                 rng=None):
        # There's probably no need to actually store these as you can't
        # access them directly in pynn anyway
        sim = get_simulator()
        machine_ts = sim.machine_time_step
        time_convert_ms = MICRO_TO_MILLISECOND_CONVERSION / machine_ts
        self.__mean = mean
        self.__stdev = stdev
        self.__start = start * time_convert_ms
        self.__stop = stop * time_convert_ms
        self.__dt = dt * time_convert_ms
        self.__rng = rng

        # Error if dt is not the same as machine time step
        if dt != (1 / time_convert_ms):
            msg = ("Only currently supported for dt = machine_time_step"
                   ", here dt = {} and machine_time_step = {}".format(
                       dt, 1 / time_convert_ms))
            raise SpynnakerException(msg)

        self.__parameter_types = dict()
        self.__parameter_types['mean'] = DataType.S1615
        self.__parameter_types['stdev'] = DataType.S1615
        self.__parameter_types['start'] = DataType.UINT32
        self.__parameter_types['stop'] = DataType.UINT32
        self.__parameter_types['dt'] = DataType.S1615
        self.__parameter_types['seed'] = DataType.UINT32

        self.__parameters = dict()
        self.__parameters['mean'] = self.__mean
        self.__parameters['stdev'] = self.__stdev
        self.__parameters['start'] = self.__start
        self.__parameters['stop'] = self.__stop
        self.__parameters['dt'] = self.__dt
        self.__parameters['seed'] = utility_calls.create_mars_kiss_seeds(
            self.__rng)

        super().__init__()

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
        if self.app_vertex is not None:
            for m_vertex in self.app_vertex.machine_vertices:
                m_vertex.set_reload_required(True)

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
        return CurrentSourceIDs.NOISY_CURRENT_SOURCE.value

    @overrides(AbstractCurrentSource.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self):
        """ The sdram usage of the current source.

        :rtype: int
        """
        # 3 because the seed parameter has length 4
        return (len(self.__parameters) + 3) * BYTES_PER_WORD
