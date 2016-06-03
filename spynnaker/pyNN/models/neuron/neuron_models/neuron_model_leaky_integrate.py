from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.abstract_neuron_model \
    import AbstractNeuronModel

from data_specification.enums.data_type import DataType

import numpy
from spynnaker.pyNN.utilities import utility_calls


class NeuronModelLeakyIntegrate(AbstractNeuronModel):

    def __init__(self, bag_of_neurons):
        AbstractNeuronModel.__init__(self)
        self._n_neurons = len(bag_of_neurons)
        self._atoms = bag_of_neurons

        for atom in self._atoms:
            if atom.get('v_init') is None:
                atom.set_param('v_init', atom.get('v_rest'))

    @property
    def v_init(self):
        return self._v_init

    def initialize_v(self, v_init):
        v_init = utility_calls.convert_param_to_numpy(
            v_init, self._n_neurons)
        for atom, value in zip(self._atoms, v_init):
            atom.set_param('v_init', value)

    @property
    def v_rest(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("v_rest"))
        return data

    @property
    def tau_m(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("tau_m"))
        return data

    @property
    def cm(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("cm"))
        return data

    @property
    def i_offset(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("i_offset"))
        return data

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
            NeuronParameter(self._atoms[atom_id].get("v_init"),
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
