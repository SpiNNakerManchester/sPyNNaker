from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from .spike_injector_vertex import SpikeInjectorVertex

_population_parameters = {
    "port": None,
    "virtual_key": None
}


class SpikeInjector(AbstractPyNNModel):

    default_population_parameters = _population_parameters

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, constraints, port, virtual_key):
        return SpikeInjectorVertex(
            n_neurons, label, constraints, port, virtual_key)
