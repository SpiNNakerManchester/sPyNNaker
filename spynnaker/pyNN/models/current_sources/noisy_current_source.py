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
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.exceptions import SpynnakerException
from .abstract_current_source import AbstractCurrentSource, CurrentSourceIDs


class NoisyCurrentSource(AbstractCurrentSource):
    """ A noisy current source beginning at "start" and ending at "stop", with
        noise simulated based on the given mean and stdev, and updating every
        dt (dt should default to the machine time step)

    """
    __slots__ = [
        "__start",
        "__stop",
        "__amplitude",
        "__offset",
        "__frequency",
        "__phase",
        "__parameters"]

    def __init__(self, mean=0.0, stdev=0.0, start=0.0, stop=0.0, dt=1.0):
        # There's probably no need to actually store these as you can't
        # access them directly in pynn anyway
        self.__mean = mean
        self.__stdev = stdev
        self.__start = start
        self.__stop = stop
        self.__dt = dt

        # should we access machine time step here to check it "fits" with dt?

        self.__parameters = dict()
        self.__parameters['mean'] = self.__mean
        self.__parameters['stdev'] = self.__stdev
        self.__parameters['start'] = self.__start
        self.__parameters['stop'] = self.__stop
        self.__parameters['dt'] = self.__dt

    def set_parameters(self, parameters):
        """ Set the current source parameters

        :param dict(str, Any) parameters: the parameters to set
        """
        for key, value in parameters.items():
            if key not in self.__parameters.keys():
                # throw an exception
                msg = "{} is not a parameter of {}".format(key, self)
                raise SpynnakerException(msg)
            else:
                self.__parameters[key] = value

    def get_parameters(self):
        """ Get the parameters of the current source

        :rtype dict(str, Any)
        """
        return self.__parameters

    def current_source_id(self):
        """ The ID of the current source.

        :rtype: int
        """
        return CurrentSourceIDs.NOISY_CURRENT_SOURCE.value
