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

from six import add_metaclass

from pacman.model.graphs.machine import MachineVertex
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractReadParametersBeforeSet(object):
    """ A vertex whose parameters must be read before any can be set.
    """

    __slots__ = ()

    _WRONG_VERTEX_TYPE_ERROR = (
        "The vertex {} is not of type MachineVertex. By not being a "
        "machine vertex, the sPyNNaker population set function may not "
        "work correctly.")

    def __new__(cls, *args, **kwargs):
        if not issubclass(cls, MachineVertex):
            raise ConfigurationException(
                cls._WRONG_VERTEX_TYPE_ERROR.format(cls))
        return super(AbstractReadParametersBeforeSet, cls).__new__(cls)

    @abstractmethod
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):
        """ Read the parameters from the machine before any are changed.

        :param ~spinnman.transceiver.Transceiver transceiver:
            the SpinnMan interface
        :param ~pacman.model.placements.Placement placement:
            the placement of a vertex
        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the slice of atoms for this vertex
        :rtype: None
        """
