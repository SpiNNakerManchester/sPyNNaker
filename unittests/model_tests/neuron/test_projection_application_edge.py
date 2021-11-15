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

from pacman.model.graphs.common import Slice
from pacman.model.graphs.machine import MachineEdge
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.neural_projections import ProjectionApplicationEdge
from pacman.model.graphs.machine import SimpleMachineVertex
from spynnaker.pyNN.models.neural_projections import SynapseInformation


def test_slices():
    unittest_setup()
    s_info = SynapseInformation(
        None, None, None, False, False, None, None, None, None, False, False,
        None, None)
    app_edge = ProjectionApplicationEdge(None, None, s_info)
    mv0_2 = SimpleMachineVertex(None, None, None, None, Slice(0, 1))
    mv2_4 = SimpleMachineVertex(None, None, None, None, Slice(2, 3))
    mv4_6 = SimpleMachineVertex(None, None, None, None, Slice(4, 5))
    app_edge.remember_associated_machine_edge(MachineEdge(mv0_2, mv2_4))
    app_edge.remember_associated_machine_edge(MachineEdge(mv4_6, mv0_2))
    app_edge.remember_associated_machine_edge(MachineEdge(mv0_2, mv2_4))
    assert app_edge.pre_slices == [Slice(0, 1), Slice(4, 5)]
    post1 = app_edge.post_slices
    assert post1 == [Slice(0, 1), Slice(2, 3)]
    app_edge.remember_associated_machine_edge(MachineEdge(mv0_2, mv0_2))
    app_edge.remember_associated_machine_edge(MachineEdge(mv2_4, mv2_4))
    assert app_edge.pre_slices == [Slice(0, 1), Slice(2, 3), Slice(4, 5)]
    post2 = app_edge.post_slices
    assert post1 == post2
    assert id(post1) != id(post2)
