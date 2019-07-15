from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from .spike_source_array_vertex import SpikeSourceArrayVertex


class SpikeSourceArray(AbstractPyNNModel):

    default_population_parameters = {}

    def __init__(self, spike_times=[]):
        self.__spike_times = spike_times

    @overrides(AbstractPyNNModel.create_vertex)
    def create_vertex(
            self, n_neurons, label, constraints):
        max_atoms = self.get_max_atoms_per_core()
        return SpikeSourceArrayVertex(
            n_neurons, self.__spike_times, constraints, label, max_atoms, self)

    @property
    def _spike_times(self):
        return self.__spike_times
