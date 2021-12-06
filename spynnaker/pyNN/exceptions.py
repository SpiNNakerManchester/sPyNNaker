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

from spinn_front_end_common.utilities.exceptions import ConfigurationException


class SpynnakerException(Exception):
    """ Superclass of all exceptions from the PyNN module.
    """


class MemReadException(SpynnakerException):
    """ Raised when the PyNN front end fails to read a certain memory region.
    """


class FilterableException(SpynnakerException):
    """ Raised when it is not possible to determine if an edge should be\
        filtered.
    """


class SynapticConfigurationException(ConfigurationException):
    """ Raised when the synaptic manager fails for some reason.
    """


class SynapticBlockGenerationException(ConfigurationException):
    """ Raised when the synaptic manager fails to generate a synaptic block.
    """


class SynapticBlockReadException(ConfigurationException):
    """ Raised when the synaptic manager fails to read a synaptic block or\
        convert it into readable values.
    """


class SynapticMaxIncomingAtomsSupportException(ConfigurationException):
    """ Raised when a synaptic sublist exceeds the max atoms possible to be\
        supported.
    """


class DelayExtensionException(ConfigurationException):
    """ Raised when a delay extension vertex fails.
    """


class SpynnakerSplitterConfigurationException(ConfigurationException):
    """ Raised when a splitter configuration fails.
    """


class InvalidParameterType(SpynnakerException):
    """ Raised when a parameter is not recognised.
    """


class SynapseRowTooBigException(SpynnakerException):
    """ Raised when a synapse row is bigger than is allowed.
    """
    def __init__(self, max_size, message):
        """
        :param max_size: the maximum permitted size of row
        :param message: the excepton message
        """
        super().__init__(message)
        self._max_size = max_size

    @property
    def max_size(self):
        """ The maximum size allowed.
        """
        return self._max_size
