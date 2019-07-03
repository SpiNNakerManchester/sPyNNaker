from .spike_source_poisson_vertex import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel

_population_parameters = {"seed": None}

DEFAULT_MAX_ATOMS_PER_CORE = 500


class SpikeSourcePoissonVariable(AbstractPyNNModel):

    default_population_parameters = _population_parameters

    def __init__(self, rates=[1.0], starts=[0], durations=None):
        self._rates = rates
        self._starts = starts
        self._durations = durations

    @classmethod
    def set_model_max_atoms_per_core(cls, n_atoms=DEFAULT_MAX_ATOMS_PER_CORE):
        super(SpikeSourcePoissonVariable, cls).set_model_max_atoms_per_core(
            n_atoms)

    @classmethod
    def get_max_atoms_per_core(cls):
        if cls not in super(
                SpikeSourcePoissonVariable, cls)._max_atoms_per_core:
            return DEFAULT_MAX_ATOMS_PER_CORE
        return super(SpikeSourcePoissonVariable, cls).get_max_atoms_per_core()

    def create_vertex(self, n_neurons, label, constraints, seed):
        max_atoms = self.get_max_atoms_per_core()
        return SpikeSourcePoissonVertex(
            n_neurons, constraints, label, seed, max_atoms, self,
            rates=self._rates, starts=self._starts, durations=self._durations)
