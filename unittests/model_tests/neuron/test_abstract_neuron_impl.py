import sys
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.neuron.abstract_pynn_neuron_model import (
    DEFAULT_MAX_ATOMS_PER_CORE, AbstractPyNNNeuronModel)


class _MyPyNNModelImpl(AbstractPyNNModel):

    default_population_parameters = {}

    def create_vertex(self, n_neurons, label, constraints):
        return None


class _MyNeuronModelImpl(AbstractPyNNNeuronModel):
    pass


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
    assert(_MyPyNNModelImpl.get_max_atoms_per_core() == sys.maxsize)
