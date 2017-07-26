from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from .abstract_neuron_impl import AbstractNeuronImpl


class NeuronImplStandard(AbstractNeuronImpl, AbstractContainsUnits):
    """ The standard implementation of the neuron model
    """

    def __init__(self):
        AbstractNeuronImpl.__init__(self)
        AbstractContainsUnits.__init__(self)
        self._units = {}

    def get_global_weight_scale(self):
        return 1.0

    def get_n_neuron_impl_parameters(self):
        return 4

    def get_neuron_impl_parameters(self):
        return []

    def get_neuron_impl_parameter_types(self):
        return []

    def get_n_cpu_cycles_per_neuron(self, n_neuron_impl):
        return 0

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
