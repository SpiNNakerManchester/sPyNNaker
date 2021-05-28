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

from enum import Enum
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


# Hashes of the current sources currently supported
class CurrentSourceIDs(Enum):
    NO_SOURCE = 0
    DC_SOURCE = 1
    AC_SOURCE = 2
    STEP_CURRENT_SOURCE = 3
    NOISY_CURRENT_SOURCE = 4


class AbstractCurrentSource(object, metaclass=AbstractBase):
    """ A simplified version of the PyNN class, since in most cases we work
        out the actual offset value on the SpiNNaker machine itself based on
        the parameters during the run.

    """
    __slots__ = ()

    def inject_into(self, cells):
        """ Inject this source into the specified population cells

        :param pop/pop_base/view cells: The cells to inject the source into
        """
        # Call the population method to pass the source in
        cells.inject(self)

    @abstractmethod
    def set_parameters(self, **parameters):
        """ Set the current source parameters

        :param parameters: the parameters to set
        """

    @abstractproperty
    def get_parameters(self):
        """ Get the parameters of the current source

        :rtype dict(str, Any)
        """

    @abstractproperty
    def get_parameter_types(self):
        """ Get the parameter types for the current source

        :rtype dict(str, Any)
        """

    @abstractproperty
    def current_source_id(self):
        """ The ID of the current source.

        :rtype: int
        """

    @abstractmethod
    def get_sdram_usage_in_bytes(self):
        """ The sdram usage in bytes of the current source.

        :rtype: int
        """
