from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.input_types.abstract_input_type \
    import AbstractInputType


class InputTypeConductance(AbstractInputType):
    """ The conductance input type
    """

    @staticmethod
    def default_parameters():
        return {'e_rev_E': 0.0, 'e_rev_I': -70.0}

    @staticmethod
    def fixed_parameters():
        return {}

    @staticmethod
    def state_variables():
        return list()

    @staticmethod
    def is_array_parameters():
        return {}

    def __init__(self, bag_of_neurons):
        AbstractInputType.__init__(self, bag_of_neurons)
        self._n_neurons = len(bag_of_neurons)

    @property
    def e_rev_E(self):
        return self._get_param("e_rev_E", self._atoms)

    @property
    def e_rev_I(self):
        return self._get_param("e_rev_I", self._atoms)

    def get_global_weight_scale(self):
        return 1024.0

    def get_n_input_type_parameters(self):
        return 2

    def get_input_type_parameters(self, atom_id):
        return [
            NeuronParameter(self._atoms[atom_id].get("e_rev_E"),
                            DataType.S1615),
            NeuronParameter(self._atoms[atom_id].get("e_rev_I"),
                            DataType.S1615)
        ]

    def get_n_cpu_cycles_per_neuron(self, n_synapse_types):
        return 10
