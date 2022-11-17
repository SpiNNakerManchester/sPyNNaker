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
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from .spike_source_array_vertex import SpikeSourceArrayVertex


class SpikeSourceArray(AbstractPyNNModel):

    default_population_parameters = {
        "splitter": None, "n_colour_bits": None}

    def __init__(self, spike_times=None):
        if spike_times is None:
            spike_times = []
        self.__spike_times = spike_times

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=default_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, splitter, n_colour_bits):
        # pylint: disable=arguments-differ
        max_atoms = self.get_model_max_atoms_per_dimension_per_core()
        return SpikeSourceArrayVertex(
            n_neurons, self.__spike_times, label, max_atoms, self, splitter,
            n_colour_bits)

    @property
    def _spike_times(self):
        return self.__spike_times
