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

from spinn_utilities.overrides import overrides
from pacman.model.graphs.application import ApplicationEdge
from pacman.model.partitioner_interfaces import AbstractSlicesConnect


class DelayAfferentApplicationEdge(ApplicationEdge, AbstractSlicesConnect):
    __slots__ = ()

    def __init__(self, pre_vertex, delay_vertex, label=None):
        """
        :param AbstractPopulationVertex pre_vertex:
        :param DelayExtensionVertex delay_vertex:
        :param str label:
        """
        super().__init__(pre_vertex, delay_vertex, label=label)

    @overrides(AbstractSlicesConnect.could_connect)
    def could_connect(self, src_machine_vertex, dest_machine_vertex):
        pre_slice = src_machine_vertex.vertex_slice
        post_slice = dest_machine_vertex.vertex_slice
        return ((pre_slice.lo_atom == post_slice.lo_atom) and
                (post_slice.hi_atom == pre_slice.hi_atom))
