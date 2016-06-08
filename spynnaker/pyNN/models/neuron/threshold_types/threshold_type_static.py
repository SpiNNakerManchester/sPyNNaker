from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neuron.threshold_types.abstract_threshold_type \
    import AbstractThresholdType


class ThresholdTypeStatic(AbstractThresholdType):
    """ A threshold that is a static value
    """

    @staticmethod
    def default_parameters():
        return {'v_thresh': -50.0}

    @staticmethod
    def fixed_parameters():
        return {}

    @staticmethod
    def state_variables():
        return []

    @staticmethod
    def is_array_parameters():
        return {}

    def __init__(self, bag_of_atoms):
        AbstractThresholdType.__init__(self)
        self._n_neurons = len(bag_of_atoms)
        self._atoms = bag_of_atoms

    @property
    def v_thresh(self):
        self._get_param('v_thresh', self._atoms)

    def get_n_threshold_parameters(self):
        return 1

    def get_threshold_parameters(self, atom_id):
        return [
            NeuronParameter(self._atoms[atom_id].get("v_thresh"),
                            DataType.S1615)
        ]

    def get_n_cpu_cycles_per_neuron(self):

        # Just a comparison, but 2 just in case!
        return 2
