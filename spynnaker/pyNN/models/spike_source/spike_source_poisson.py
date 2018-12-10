from .spike_source_poisson_vertex import SpikeSourcePoissonVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel

_population_parameters = {"seed": None}

# Technically, this is ~2900 in terms of DTCM, but is timescale dependent
# in terms of CPU (2900 at 10 times slow down is fine, but not at
# real-time)
DEFAULT_MAX_ATOMS_PER_CORE = 500


class SpikeSourcePoisson(AbstractPyNNModel):

    default_population_parameters = _population_parameters

    def __init__(self, rate=1.0, start=0, duration=None):
        self._rate = rate
        self._start = start
        self._duration = duration

    @classmethod
    def set_model_max_atoms_per_core(cls, n_atoms=DEFAULT_MAX_ATOMS_PER_CORE):
        super(SpikeSourcePoisson, cls).set_model_max_atoms_per_core(
            n_atoms)

    @classmethod
    def get_max_atoms_per_core(cls):
        if cls not in super(SpikeSourcePoisson, cls)._max_atoms_per_core:
            return DEFAULT_MAX_ATOMS_PER_CORE
        return super(SpikeSourcePoisson, cls).get_max_atoms_per_core()

    def create_vertex(self, n_neurons, label, constraints, seed):
        max_atoms = self.get_max_atoms_per_core()
        return SpikeSourcePoissonVertex(
            n_neurons, constraints, label, seed, max_atoms, self,
            rate=self._rate, start=self._start, duration=self._duration)
