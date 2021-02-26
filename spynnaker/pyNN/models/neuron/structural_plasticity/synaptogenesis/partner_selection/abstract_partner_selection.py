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

from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


class AbstractPartnerSelection(object, metaclass=AbstractBase):
    """ A partner selection rule
    """

    __slots__ = ()

    @abstractproperty
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule

        :rtype: str
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self):
        """ Get the amount of SDRAM used by the parameters of this rule

        :rtype: str
        """

    @abstractmethod
    def write_parameters(self, spec):
        """ Write the parameters of the rule to the spec

        :param ~data_specification.DataSpecificationGenerator spec:
        """

    @abstractmethod
    def get_parameter_names(self):
        """ Return the names of the parameters supported by this rule

        :rtype: iterable(str)
        """
