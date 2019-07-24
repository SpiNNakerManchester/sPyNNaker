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

from pacman.model.graphs.application import ApplicationEdge
from .delay_afferent_machine_edge import DelayAfferentMachineEdge


class DelayAfferentApplicationEdge(ApplicationEdge):
    __slots__ = ()

    def __init__(self, prevertex, delayvertex, label=None):
        super(DelayAfferentApplicationEdge, self).__init__(
            prevertex, delayvertex, label=label)

    def create_machine_edge(self, pre_vertex, post_vertex, label):
        return DelayAfferentMachineEdge(pre_vertex, post_vertex, label)
