# Copyright (c) 2017-2020 The University of Manchester
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
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.machine.machine_vertex import MachineVertex

NEURON_EXPANDER_APLX = "neuron_expander.aplx"


@require_subclass(MachineVertex)
class AbstractNeuronExpandable(object, metaclass=AbstractBase):
    """ Indicates a class (a \
        :py:class:`~pacman.model.graphs.machine.MachineVertex`) \
        that has may need to run the NEURON_EXPANDER aplx
    """

    __slots__ = ()

    @abstractmethod
    def gen_neurons_on_machine(self):
        """ True if the neurons of a the slice of this vertex should be \
            generated on the machine.

        .. note::
            The typical implementation for this method will be to ask the
            neuron data

        :rtype: bool
        """

    @abstractproperty
    def neuron_generator_region(self):
        """ The region containing the parameters of neuron expansion

        :rtype: int
        """

    @abstractmethod
    def read_generated_initial_values(self, placement):
        """ Fill in any requested initial values

        :param ~pacman.model.placements.Placement placement:
            Where the data is on the machine
        """
