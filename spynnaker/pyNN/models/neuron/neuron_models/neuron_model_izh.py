from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.abstract_neuron_model \
    import AbstractNeuronModel

from data_specification.enums.data_type import DataType


class NeuronModelIzh(AbstractNeuronModel):

    def __init__(self, bag_of_neurons):

        AbstractNeuronModel.__init__(self)
        self._n_neurons = len(bag_of_neurons)
        self._atoms = bag_of_neurons

    @property
    def a(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("a"))
        return data

    @property
    def b(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("b"))
        return data

    @property
    def c(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("c"))
        return data

    @property
    def d(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("d"))
        return data

    @property
    def v_init(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("v_init"))
        return data

    @property
    def u_init(self):
        data = list()
        for atom in self._atoms:
            data.append(atom.get("u_init"))
        return data

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
            NeuronParameter(self._atoms[atom_id].get('v_init'), DataType.S1615),

            # REAL U
            NeuronParameter(self._atoms[atom_id].get('u_init'), DataType.S1615),

            # offset current [nA]
            # REAL I_offset;
            NeuronParameter(self._atoms[atom_id].get('i_offset'),
                            DataType.S1615),

            # current timestep - simple correction for threshold
            # REAL this_h;
            NeuronParameter(
                self._atoms[atom_id].get('machine_time_step') / 1000.0,
                DataType.S1615)
        ]

    def get_n_global_parameters(self):
        return 1

    def get_global_parameters(self):
        return [
            NeuronParameter(
                self._atoms[0].get('machine_time_step') / 1000.0,
                DataType.S1615)
        ]

    def get_n_cpu_cycles_per_neuron(self):
        # A bit of a guess
        return 150
