from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import get_exponential_decay_and_init
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type \
    import AbstractSynapseType

from data_specification.enums.data_type import DataType


class SynapseTypeDualExponential(AbstractSynapseType):

    def __init__(self, bag_of_neurons):
        AbstractSynapseType.__init__(self)
        self._n_neurons = len(bag_of_neurons)
        self._atoms = bag_of_neurons

    @property
    def tau_syn_E(self):
        return self._get_param("tau_syn_E", self._atoms)

    @property
    def tau_syn_E2(self):
        return self._get_param("tau_syn_E2", self._atoms)

    @property
    def tau_syn_I(self):
        return self._get_param("tau_syn_I", self._atoms)

    def get_n_synapse_types(self):
        return 3

    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "excitatory2":
            return 1
        elif target == "inhibitory":
            return 2
        return None

    def get_synapse_targets(self):
        return "excitatory", "excitatory2", "inhibitory"

    def get_n_synapse_type_parameters(self):
        return 6

    def get_synapse_type_parameters(self, atom_id):
        e_decay, e_init = get_exponential_decay_and_init(
            self._atoms[atom_id].get("tau_syn_E"),
            self._atoms[atom_id].population_parameters["machine_time_step"])
        e_decay2, e_init2 = get_exponential_decay_and_init(
            self._atoms[atom_id].get("tau_syn_E2"),
            self._atoms[atom_id].population_parameters["machine_time_step"])
        i_decay, i_init = get_exponential_decay_and_init(
            self._atoms[atom_id].get("tau_syn_I"),
            self._atoms[atom_id].population_parameters["machine_time_step"])

        return [
            NeuronParameter(e_decay, DataType.UINT32),
            NeuronParameter(e_init, DataType.UINT32),
            NeuronParameter(e_decay2, DataType.UINT32),
            NeuronParameter(e_init2, DataType.UINT32),
            NeuronParameter(i_decay, DataType.UINT32),
            NeuronParameter(i_init, DataType.UINT32)
        ]

    def get_n_cpu_cycles_per_neuron(self):

        # A guess
        return 100
