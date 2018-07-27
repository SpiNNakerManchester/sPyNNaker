from spynnaker.pyNN.models.spike_source.spike_source_poisson_base \
    import SpikeSourcePoissonBase


class SpikeSourcePoissonVariable(SpikeSourcePoissonBase):

    # parameters expected by PyNN
    default_parameters = {
        'starts': [0.0], 'durations': None, 'rates': [1.0]}

    # parameters expected by spinnaker
    non_pynn_default_parameters = {
        'constraints': None, 'seed': None, 'label': None}

    # Technically, this is ~2900 in terms of DTCM, but is timescale dependent
    # in terms of CPU (2900 at 10 times slow down is fine, but not at
    # real-time)
    DEFAULT_MAX_ATOMS_PER_CORE = 500
    _model_based_max_atoms_per_core = DEFAULT_MAX_ATOMS_PER_CORE

    def __init__(
            self, n_neurons, constraints, label, rates, seed=None,
            starts=None, durations=None, max_rate=None):
        SpikeSourcePoissonBase.__init__(
            self, n_neurons, "SpikeSourcePoissonVariable", constraints, label,
            max_atoms_per_core=self.get_max_atoms_per_core(),
            seed=seed, rates=rates, starts=starts, durations=durations,
            max_rate=max_rate)

    @staticmethod
    def set_model_max_atoms_per_core(new_value=DEFAULT_MAX_ATOMS_PER_CORE):
        SpikeSourcePoissonVariable._model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_max_atoms_per_core():
        return SpikeSourcePoissonVariable._model_based_max_atoms_per_core

    @property
    def rates(self):
        return self._data["rates"]

    @rates.setter
    def rates(self, rates):
        if hasattr(rates[0], "__len__"):
            self._data["rates"] = rates
        else:
            self._data["rates"].set_value(rates, use_list_as_value=True)

    @property
    def starts(self):
        return self._data["starts"]

    @starts.setter
    def starts(self, starts):
        if hasattr(starts[0], "__len__"):
            self._data["starts"] = starts
        else:
            self._data["starts"].set_value(starts, use_list_as_value=True)

    @property
    def durations(self):
        return self._data["durations"]

    @durations.setter
    def durations(self, durations):
        if hasattr(durations[0], "__len__"):
            self._data["durations"] = durations
        else:
            self._data["durations"].set_value(
                durations, use_list_as_value=True)
