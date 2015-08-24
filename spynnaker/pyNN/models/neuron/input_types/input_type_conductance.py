from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.input_types.abstract_input_type \
    import AbstractInputType


class InputTypeConductance(AbstractInputType):
    """ The conductance input type
    """

    def __init__(self, e_rev_E, e_rev_I):
        AbstractInputType.__init__(self)
        self._e_rev_E = e_rev_E
        self._e_rev_I = e_rev_I

    @property
    def e_rev_E(self):
        return self._e_rev_E

    @e_rev_E.setter
    def e_rev_E(self, e_rev_E):
        self._e_rev_E = e_rev_E

    @property
    def e_rev_I(self):
        return self._e_rev_I

    @e_rev_I.setter
    def e_rev_I(self, e_rev_I):
        self._e_rev_I = e_rev_I

    def get_global_weight_scale(self):
        return 1024.0

    def get_n_input_type_parameters(self):
        return 2

    def get_input_type_parameters(self):
        return [
            NeuronParameter(self._e_rev_E, DataType.S1615),
            NeuronParameter(self._e_rev_I, DataType.S1615)
        ]

    def get_n_cpu_cycles_per_neuron(self):
        return 10
