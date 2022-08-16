# Copyright (c) 2020 The University of Manchester
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

from pacman.model.constraints.key_allocator_constraints import (
    FixedKeyAndMaskConstraint)
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.utility_models import (
    ReverseIPTagMulticastSourceMachineVertex)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.utility_models.delays import (
    DelayExtensionMachineVertex)


class KeyConstraintAdder(object):

    def __call__(self):
        for partition in SpynnakerDataView.iterate_partitions():
            for vertex in partition.pre_vertex.splitter.get_out_going_vertices(
                    partition.identifier):
                if isinstance(
                        vertex, ReverseIPTagMulticastSourceMachineVertex):
                    if vertex.vertex_slice.lo_atom == 0:
                        vertex.add_constraint(
                            FixedKeyAndMaskConstraint(
                                [BaseKeyAndMask(
                                    base_key=0, mask=0xFFFFFFc0)]))
                    else:
                        vertex.add_constraint(
                            FixedKeyAndMaskConstraint(
                                [BaseKeyAndMask(
                                    base_key=64, mask=0xFFFFFFc0)]))
                elif isinstance(vertex, DelayExtensionMachineVertex):
                    if vertex.vertex_slice.lo_atom == 0:
                        vertex.add_constraint(
                            FixedKeyAndMaskConstraint(
                                [BaseKeyAndMask(
                                    base_key=128, mask=0xFFFFFFc0)]))
                    else:
                        vertex.add_constraint(
                            FixedKeyAndMaskConstraint(
                                [BaseKeyAndMask(
                                    base_key=192, mask=0xFFFFFFc0)]))
