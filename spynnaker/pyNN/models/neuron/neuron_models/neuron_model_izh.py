from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.abstract_neuron_model \
    import AbstractNeuronModel

from data_specification.enums.data_type import DataType
from spynnaker.pyNN.utilities import utility_calls


class NeuronModelIzh(AbstractNeuronModel):

    def __init__(self, bag_of_neurons):

        AbstractNeuronModel.__init__(self)
        self._n_neurons = len(bag_of_neurons)
        self._atoms = bag_of_neurons

        # check for state variables in the basic config params
        for atom in self._atoms:
            if atom.get_state_variable('v') is None:
                if atom.get('v_init') is not None:
                    atom.initialize('v', atom.get('v_init'))
                atom.remove_param('v_init')
        for atom in self._atoms:
            if atom.get_state_variable('u') is None:
                if atom.get('u_init') is not None:
                    atom.initialize('u', atom.get('u_init'))
                atom.remove_param('u_init')

    @property
    def a(self):
        return self._get_param('a', self._atoms)

    @property
    def b(self):
        return self._get_param('b', self._atoms)

    @property
    def c(self):
        return self._get_param('c', self._atoms)

    @property
    def d(self):
        return self._get_param('d', self._atoms)

    @property
    def v_init(self):
        return self._get_state_variable('v', self._atoms)

    @property
    def u_init(self):
        return self._get_state_variable('u', self._atoms)

    def initialize_v(self, v_init):
        v_init = utility_calls.convert_param_to_numpy(
            v_init, self._n_neurons)
        self._set_state_variable('v', v_init, self._atoms)

    def initialize_u(self, u_init):
        u_init = utility_calls.convert_param_to_numpy(
            u_init, self._n_neurons)
        self._set_state_variable('u', u_init, self._atoms)

    def get_n_neural_parameters(self):
        return 8

    def get_neural_parameters(self, atom_id):
        return [

            # REAL A
            NeuronParameter(self._atoms[atom_id].get('a'), DataType.S1615),

            # REAL B
            NeuronParameter(self._atoms[atom_id].get('b'), DataType.S1615),

            # REAL C
            NeuronParameter(self._atoms[atom_id].get('c'), DataType.S1615),

            # REAL D
            NeuronParameter(self._atoms[atom_id].get('d'), DataType.S1615),

            # REAL V
            NeuronParameter(self._atoms[atom_id].get_state_variable('v'),
                            DataType.S1615),

            # REAL U
            NeuronParameter(self._atoms[atom_id].get_state_variable('u'),
                            DataType.S1615),

            # offset current [nA]
            # REAL I_offset;
            NeuronParameter(self._atoms[atom_id].get('i_offset'),
                            DataType.S1615),

            # current timestep - simple correction for threshold
            # REAL this_h;
            NeuronParameter(
                self._atoms[atom_id].population_parameters[
                    'machine_time_step'] / 1000.0,
                DataType.S1615)
        ]

    def get_n_global_parameters(self):
        return 1

    def get_global_parameters(self):
        return [
            NeuronParameter(
                self._atoms[0].population_parameters[
                    'machine_time_step'] / 1000.0,
                DataType.S1615)
        ]

    def get_n_cpu_cycles_per_neuron(self):
        # A bit of a guess
        return 150
