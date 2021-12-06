# Copyright (c) 2020-2021 The University of Manchester
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
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from pacman.model.graphs import AbstractSupportsSDRAMEdges
from spinn_front_end_common.utilities.constants import BYTES_PER_SHORT


@add_metaclass(AbstractBase)
class ReceivesSynapticInputsOverSDRAM(AbstractSupportsSDRAMEdges):
    """ An object that receives synaptic inputs over SDRAM.

        The number of neurons to be sent per synapse type is rounded up to be
        a power of 2.  A sender must send N_BYTES_PER_INPUT of data for each
        synapse type for each neuron, formatted as all the data for each neuron
        for the first synapse type, followed by all the data for each neuron
        for the second, and so on for each synapse type.  Each input is an
        accumulated weight value for the timestep, scaled with the given weight
        scales.
    """

    # The size of each input in bytes
    N_BYTES_PER_INPUT = BYTES_PER_SHORT

    @abstractproperty
    def n_target_neurons(self):
        """ The number of neurons expecting to receive input

        :rtype: int
        """

    @abstractproperty
    def n_target_synapse_types(self):
        """ The number of synapse types expecting to receive input

        :rtype: int
        """

    @abstractproperty
    def weight_scales(self):
        """ A list of scale factors to be applied to weights that get passed
            over SDRAM, one for each synapse type.

        :rtype: list(int)
        """

    @abstractproperty
    def n_bytes_for_transfer(self):
        """ The number of bytes to be sent over the channel.  This will be
            calculated using the above numbers, but also rounded up to a number
            of words, and with the number of neurons rounded up to a power of 2

        :rtype: int
        """
