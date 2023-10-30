# Copyright (c) 2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import numpy
from pacman.model.graphs.application import ApplicationVertex
from spynnaker.pyNN.models.neural_projections.connectors import (
    AbstractConnector)

class SimpleVertex(ApplicationVertex):

    def __init__(self, max_atoms_per_core, atoms_shape):
        super(SimpleVertex, self).__init__(
            max_atoms_per_core=max_atoms_per_core)
        self.__atoms_shape = atoms_shape

    @property
    def n_atoms(self):
        return numpy.prod(self.__atoms_shape)

    @property
    def atoms_shape(self):
        return self.__atoms_shape


class SimpleConnector(AbstractConnector):

    def get_delay_minimum(self, synapse_info):
        return None

    def get_delay_maximum(self, synapse_info):
        return None

    def get_n_connections_from_pre_vertex_maximum(
            self, n_post_atoms, synapse_info, min_delay=None, max_delay=None):
        return None

    def get_n_connections_to_post_vertex_maximum(self, synapse_info):
        return None

    def get_weight_maximum(self, synapse_info):
        return None


def test_get_row_indices():
    conn = SimpleConnector()
    vtx = SimpleVertex((3, 3), (6, 6))
    # From the interdimensional compatibility documentation diagram, we can
    # check we get what we expect
    first_half_indices = conn._get_row_indices(numpy.arange(18), vtx)
    assert numpy.array_equal(
        first_half_indices,
        [0, 1, 2, 9, 10, 11, 3, 4, 5, 12, 13, 14, 6, 7, 8, 15, 16, 17])


if __name__ == "__main__":
    test_get_row_indices()
