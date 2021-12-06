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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.machine import MachineVertex


@require_subclass(MachineVertex)
class AbstractMaxSpikes(object, metaclass=AbstractBase):
    """ Indicates a class (a \
        :py:class:`~pacman.model.graphs.machine.MachineVertex`) \
        that can describe the maximum rate that it sends spikes.

        The :py:class:`~.SynapticManager` assumes that all machine vertexes
        share the same synapse_information will have the same rates.
    """

    __slots__ = ()

    @abstractmethod
    def max_spikes_per_ts(self):
        """ Get maximum expected number of spikes per timestep

        :rtype: int
        """

    @abstractmethod
    def max_spikes_per_second(self):
        """ Get maximum expected number of spikes per second

        :param str variable: the variable to find units from
        :return: the units as a string.
        :rtype: str
        """
