from data_specification.enums import DataType
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType
from spynnaker.pyNN.utilities.ranged.spynakker_ranged_dict import \
    SpynakkerRangeDictionary

INITIAL_INPUT_EXC = "initial_input_exc"
INITIAL_INPUT_INH = "initial_input_inh"


class SynapseTypeDelta(AbstractSynapseType):
    """ This represents a synapse type with two delta synapses
    """
    __slots__ = [
        "_data"]

    def __init__(self, n_neurons, initial_input_exc, initial_input_inh):
        AbstractSynapseType.__init__(self)
        self._data = SpynakkerRangeDictionary(size=n_neurons)
        self._data[INITIAL_INPUT_EXC] = initial_input_exc
        self._data[INITIAL_INPUT_INH] = initial_input_inh

    def get_n_synapse_types(self):
        return 2

    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        return None

    def get_synapse_targets(self):
        return "excitatory", "inhibitory"

    def get_n_synapse_type_parameters(self):
        return 2

    def get_synapse_type_parameters(self):
        return [
            NeuronParameter(self._data[INITIAL_INPUT_EXC], DataType.S1615),
            NeuronParameter(self._data[INITIAL_INPUT_INH], DataType.S1615)
        ]

    def get_synapse_type_parameter_types(self):
        return []

    def get_n_cpu_cycles_per_neuron(self):
        return 0

    @property
    def isyn_exc(self):
        return self._data[INITIAL_INPUT_EXC]

    @isyn_exc.setter
    def isyn_exc(self, new_value):
        self._data.set_value(key=INITIAL_INPUT_EXC, value=new_value)

    @property
    def isyn_inh(self):
        return self._data[INITIAL_INPUT_INH]

    @isyn_inh.setter
    def isyn_inh(self, new_value):
        self._data.set_value(key=INITIAL_INPUT_INH, value=new_value)
