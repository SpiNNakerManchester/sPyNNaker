from pacman.model.decorators.overrides import overrides
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.neuron.pynn_partition_vertex import PyNNPartitionVertex

import math

#Must be a power of 2!!!
DEFAULT_MAX_ATOMS_PER_SYN_CORE = 64
SYN_CORES_PER_NEURON_CORE = 1
DEFAULT_MAX_ATOMS_PER_NEURON_CORE = DEFAULT_MAX_ATOMS_PER_SYN_CORE * SYN_CORES_PER_NEURON_CORE

_population_parameters = {
    "spikes_per_second": None, "ring_buffer_sigma": None,
    "incoming_spike_buffer_size": None
}


class AbstractPyNNNeuronModel(AbstractPyNNModel):

    __slots__ = ("_model")

    default_population_parameters = _population_parameters

    def __init__(self, model):
        self._model = model
        self._pynn_partition_vertices = list()

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
            ring_buffer_sigma, incoming_spike_buffer_size):

        max_atoms = self.get_max_atoms_per_core()

        for i in range(2):
            self._pynn_partition_vertices.append(PyNNPartitionVertex(i, n_neurons/2, label, constraints, max_atoms,
                                                                     spikes_per_second, ring_buffer_sigma, self._model,
                                                                     self, incoming_spike_buffer_size))

        return self._pynn_partition_vertices

    def add_internal_edges_and_vertices(self, spinnaker_control):

        for i in range(2):
            self._pynn_partition_vertices[i].add_internal_edges_and_vertices(spinnaker_control)
