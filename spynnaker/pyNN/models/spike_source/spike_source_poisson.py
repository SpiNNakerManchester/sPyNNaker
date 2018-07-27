from .spike_source_poisson_base import SpikeSourcePoissonBase
import numpy


class SpikeSourcePoisson(SpikeSourcePoissonBase):

    # parameters expected by PyNN
    default_parameters = {
        'start': 0.0, 'duration': None, 'rate': 1.0}

    # parameters expected by spinnaker
    non_pynn_default_parameters = {
        'constraints': None, 'seed': None, 'label': None}

    # Technically, this is ~2900 in terms of DTCM, but is timescale dependent
    # in terms of CPU (2900 at 10 times slow down is fine, but not at
    # real-time)
    DEFAULT_MAX_ATOMS_PER_CORE = 500
    _model_based_max_atoms_per_core = DEFAULT_MAX_ATOMS_PER_CORE

    def __init__(
            self, n_neurons, constraints, label, rate, seed=None,
            start=None, duration=None, max_rate=None):
        SpikeSourcePoissonBase.__init__(
            self, n_neurons, "SpikeSourcePoisson", constraints, label,
            max_atoms_per_core=self.get_max_atoms_per_core(),
            seed=seed, rate=rate, start=start, duration=duration,
            max_rate=max_rate)

    @staticmethod
    def set_model_max_atoms_per_core(new_value=DEFAULT_MAX_ATOMS_PER_CORE):
        SpikeSourcePoisson._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return SpikeSourcePoisson._model_based_max_atoms_per_core

    @property
    def rate(self):
        return [r[0] for r in self._data["rates"]]

    @rate.setter
    def rate(self, rate):
        if hasattr(rate, "__len__"):
            self._data["rates"] = [numpy.array([r]) for r in rate]
        else:
            self._data["rates"].set_value(
                numpy.array([rate]), use_list_as_value=True)

    @property
    def start(self):
        return [s[0] for s in self._data["starts"]]

    @start.setter
    def start(self, start):
        if hasattr(start, "__len__"):
            self._data["starts"] = [numpy.array([s]) for s in start]
        else:
            self._data["starts"].set_value(
                numpy.array([start]), use_list_as_value=True)

    @property
    def duration(self):
        return [d[0] for d in self._data["durations"]]

    @duration.setter
    def duration(self, duration):
        if hasattr(duration, "__len__"):
            self._data["durations"] = [numpy.array([d]) for d in duration]
        else:
            self._data["durations"].set_value(
                numpy.array([duration]), use_list_as_value=True)
