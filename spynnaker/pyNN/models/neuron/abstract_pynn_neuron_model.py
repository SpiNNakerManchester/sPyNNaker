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

from pacman.model.decorators.overrides import overrides
from spynnaker.pyNN.models.neuron.pynn_partition_vertex import PyNNPartitionVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel

#Must be a power of 2!!!
DEFAULT_MAX_ATOMS_PER_NEURON_CORE = 64

_population_parameters = {
    "spikes_per_second": None, "ring_buffer_sigma": None,
    "incoming_spike_buffer_size": None, "in_partitions": None,
    "out_partitions": None, "n_targets": None
}


class AbstractPyNNNeuronModel(AbstractPyNNModel):
    __slots__ = ["__model"]

    default_population_parameters = _population_parameters

    def __init__(self, model):
        self.__model = model

    @property
    def _model(self):
        return self.__model

    @classmethod
    def set_model_max_atoms_per_core(cls, n_atoms=DEFAULT_MAX_ATOMS_PER_NEURON_CORE):
        super(AbstractPyNNNeuronModel, cls).set_model_max_atoms_per_core(
            n_atoms)

    @classmethod
    def get_max_atoms_per_core(cls):
        if cls not in super(AbstractPyNNNeuronModel, cls)._max_atoms_per_core:
            return DEFAULT_MAX_ATOMS_PER_NEURON_CORE
        return super(AbstractPyNNNeuronModel, cls).get_max_atoms_per_core()

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, constraints, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size,
            in_partitions, out_partitions, n_targets):

        max_atoms = self.get_max_atoms_per_core()
        
        return PyNNPartitionVertex(
            n_neurons, label, constraints, max_atoms, spikes_per_second,
            ring_buffer_sigma, self.__model, self, incoming_spike_buffer_size,
            in_partitions, out_partitions, n_targets)
