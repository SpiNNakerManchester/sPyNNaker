from spynnaker.pyNN.models.neuron.implementations.abstract_neuron_impl \
    import AbstractNeuronImpl
from spynnaker.pyNN.models.abstract_models import AbstractPyNNModel
import sys
from spynnaker.pyNN.models.neuron.implementations.abstract_neuron_impl \
    import DEFAULT_MAX_ATOMS_PER_CORE


class _MyPyNNModelImpl(AbstractPyNNModel):

    default_parameters = {}

    default_initial_values = {}

    default_population_parameters = {}

    def create_vertex(self, n_neurons, label, constraints):
        return None


class _MyNeuronModelImpl(AbstractNeuronImpl):

    @property
    def model_name(self):
        return "MyNeuronModelImpl"

    @property
    def binary_name(self):
        return "my_neuron_model_impl.aplx"

    def get_n_cpu_cycles(self, n_neurons):
        return n_neurons

    def get_dtcm_usage_in_bytes(self, n_neurons):
        return n_neurons

    def get_sdram_usage_in_bytes(self, n_neurons):
        return n_neurons

    def get_global_weight_scale(self):
        return 1.0

    def get_n_synapse_types(self):
        return 1

    def get_synapse_id_by_target(self, target):
        return 1

    def get_synapse_targets(self):
        return "excitatory"

    def get_recordable_variables(self):
        return []

    def get_recordable_units(self, variable):
        return None

    def get_recordable_variable_index(self, variable):
        return 0

    def is_recordable(self, variable):
        return False

    def add_parameters(self, parameters):
        pass

    def add_state_variables(self, state_variables):
        pass

    def get_data(self, parameters, state_variables, vertex_slice):
        pass

    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):
        return offset

    def get_units(self, variable):
        return None

    def is_conductance_based(self):
        return False


class _MyOtherNeuronModel(_MyNeuronModelImpl):
    pass


def test_max_atoms_per_core():
    _MyPyNNModelImpl.set_model_max_atoms_per_core(100)
    _MyNeuronModelImpl.set_model_max_atoms_per_core(20)
    _MyOtherNeuronModel.set_model_max_atoms_per_core(50)
    assert(_MyPyNNModelImpl.get_max_atoms_per_core() == 100)
    assert(_MyNeuronModelImpl.get_max_atoms_per_core() == 20)
    assert(_MyOtherNeuronModel.get_max_atoms_per_core() == 50)


def test_reset_max_atoms_per_core():
    _MyNeuronModelImpl.set_model_max_atoms_per_core(20)
    _MyNeuronModelImpl.set_model_max_atoms_per_core()
    _MyPyNNModelImpl.set_model_max_atoms_per_core(100)
    _MyPyNNModelImpl.set_model_max_atoms_per_core()
    assert(_MyNeuronModelImpl.get_max_atoms_per_core() ==
           DEFAULT_MAX_ATOMS_PER_CORE)
    assert(_MyPyNNModelImpl.get_max_atoms_per_core() == sys.maxint)
