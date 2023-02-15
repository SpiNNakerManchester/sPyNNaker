# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
