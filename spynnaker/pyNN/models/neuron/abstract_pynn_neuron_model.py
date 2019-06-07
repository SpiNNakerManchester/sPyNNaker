from pacman.model.decorators.overrides import overrides
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel

DEFAULT_MAX_ATOMS_PER_CORE = 255

_population_parameters = {
    "spikes_per_second": None, "ring_buffer_sigma": None,
    "incoming_spike_buffer_size": None
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
    def set_model_max_atoms_per_core(cls, n_atoms=DEFAULT_MAX_ATOMS_PER_CORE):
        super(AbstractPyNNNeuronModel, cls).set_model_max_atoms_per_core(
            n_atoms)

    @classmethod
    def get_max_atoms_per_core(cls):
        if cls not in super(AbstractPyNNNeuronModel, cls)._max_atoms_per_core:
            return DEFAULT_MAX_ATOMS_PER_CORE
        return super(AbstractPyNNNeuronModel, cls).get_max_atoms_per_core()

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, constraints, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size):
        max_atoms = self.get_max_atoms_per_core()
        return AbstractPopulationVertex(
            n_neurons, label, constraints, max_atoms, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size, self.__model, self)
