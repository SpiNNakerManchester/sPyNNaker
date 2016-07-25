from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.abstract_neuron_model \
    import AbstractNeuronModel

from data_specification.enums.data_type import DataType

import numpy
from spynnaker.pyNN.utilities import utility_calls


class NeuronModelLeakyIntegrate(AbstractNeuronModel):

    @staticmethod
    def default_parameters():
        return {'v_init': None, 'v_rest': -65.0, 'tau_m': 20.0,
                'cm': 1.0, 'i_offset': 0}

    @staticmethod
    def fixed_parameters():
        return {}

    @staticmethod
    def state_variables():
        params = list(['v'])
        return params

    @staticmethod
    def is_array_parameters():
        return {}

    def __init__(self, bag_of_neurons):
        AbstractNeuronModel.__init__(self)
        self._n_neurons = len(bag_of_neurons)
        self._atoms = bag_of_neurons

        for atom in self._atoms:
            if atom.get_state_variable('v') is None:
                if atom.get('v_init') is None:
                    atom.initialize('v', atom.get('v_rest'))
                else:
                    atom.initialize('v', atom.get('v_init'))
                atom.remove_param('v_init')

    @property
    def v_init(self):
        return self._get_state_variable('v', self._atoms)

    def initialize_v(self, v_init):
        v_init = utility_calls.convert_param_to_numpy(
            v_init, self._n_neurons)
        self._set_state_variable('v', v_init, self._atoms)

    @property
    def v_rest(self):
        return self._get_param('v_rest', self._atoms)

    @property
    def tau_m(self):
        return self._get_param('tau_m', self._atoms)

    @property
    def cm(self):
        return self._get_param('cm', self._atoms)

    @property
    def i_offset(self):
        return self._get_param('i_offset', self._atoms)

    def _r_membrane(self, atom_id):
        return self._atoms[atom_id].get("tau_m") / \
            self._atoms[atom_id].get('cm')

    def _exp_tc(self, atom_id):
        return numpy.exp(float(
            -self._atoms[atom_id].population_parameters["machine_time_step"]) /
            (1000.0 * self._atoms[atom_id].get("tau_m")))

    def get_n_neural_parameters(self):
        return 5

    def get_neural_parameters(self, atom_id):
        return [

            # membrane voltage [mV]
            # REAL     V_membrane;
            NeuronParameter(self._atoms[atom_id].get_state_variable("v"),
                            DataType.S1615),

            # membrane resting voltage [mV]
            # REAL     V_rest;
            NeuronParameter(self._atoms[atom_id].get("v_rest"),
                            DataType.S1615),

            # membrane resistance [MOhm]
            # REAL     R_membrane;
            NeuronParameter(self._r_membrane(atom_id), DataType.S1615),

            # 'fixed' computation parameter - time constant multiplier for
            # closed-form solution
            # exp( -(machine time step in ms)/(R * C) ) [.]
            # REAL     exp_TC;
            NeuronParameter(self._exp_tc(atom_id), DataType.S1615),

            # offset current [nA]
            # REAL     I_offset;
            NeuronParameter(self._atoms[atom_id].get("i_offset"),
                            DataType.S1615)
        ]

    def get_n_global_parameters(self):
        return 0

    def get_global_parameters(self):
        return []

    def get_n_cpu_cycles_per_neuron(self):

        # A bit of a guess
        return 80
