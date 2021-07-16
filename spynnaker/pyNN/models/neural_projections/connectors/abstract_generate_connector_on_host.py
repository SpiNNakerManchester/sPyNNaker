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


class AbstractGenerateConnectorOnHost(object, metaclass=AbstractBase):
    """ A connector that can be generated on host
    """

    # Mix-in class, so don't add anything here!
    __slots__ = []

    @abstractmethod
    def create_synaptic_block(
            self, pre_slices, post_slices, pre_vertex_slice, post_vertex_slice,
            synapse_type, synapse_info):
        """ Create a synaptic block from the data.

        :param weights:
        :type weights: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param delays:
        :type delays: ~numpy.ndarray or ~pyNN.random.NumpyRNG or int or float
            or list(int) or list(float)
        :param list(~pacman.model.graphs.common.Slice) pre_slices:
        :param list(~pacman.model.graphs.common.Slice) post_slices:
        :param ~pacman.model.graphs.common.Slice pre_vertex_slice:
        :param ~pacman.model.graphs.common.Slice post_vertex_slice:
        :param AbstractSynapseType synapse_type:
        :param SynapseInformation synapse_info:
        :returns:
            The synaptic matrix data to go to the machine, as a Numpy array
        :rtype: ~numpy.ndarray
        """
