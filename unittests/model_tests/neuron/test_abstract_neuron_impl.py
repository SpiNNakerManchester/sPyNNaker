# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.neuron.abstract_pynn_neuron_model import (
    DEFAULT_MAX_ATOMS_PER_CORE, AbstractPyNNNeuronModel)
from spynnaker.pyNN.models.defaults import default_initial_values, defaults


@defaults
class _MyPyNNModelImpl(AbstractPyNNModel):

    default_population_parameters = {}

    @default_initial_values({"svar"})
    def __init__(self, param=1.0, svar=2.0):
        pass

    def create_vertex(self, n_neurons, label, constraints):
        return None


class _MyNeuronModelImpl(AbstractPyNNNeuronModel):
    pass


class _MyOtherNeuronModel(_MyNeuronModelImpl):
    pass


def test_max_atoms_per_core():
    unittest_setup()
    _MyPyNNModelImpl.set_model_max_atoms_per_core(100)
    _MyNeuronModelImpl.set_model_max_atoms_per_core(20)
    _MyOtherNeuronModel.set_model_max_atoms_per_core(50)
    assert(_MyPyNNModelImpl.get_max_atoms_per_core() == 100)
    assert(_MyNeuronModelImpl.get_max_atoms_per_core() == 20)
    assert(_MyOtherNeuronModel.get_max_atoms_per_core() == 50)


def test_reset_max_atoms_per_core():
    unittest_setup()
    _MyNeuronModelImpl.set_model_max_atoms_per_core(20)
    _MyNeuronModelImpl.set_model_max_atoms_per_core()
    _MyPyNNModelImpl.set_model_max_atoms_per_core(100)
    _MyPyNNModelImpl.set_model_max_atoms_per_core()
    assert(_MyNeuronModelImpl.get_max_atoms_per_core() ==
           DEFAULT_MAX_ATOMS_PER_CORE)
    assert(_MyPyNNModelImpl.get_max_atoms_per_core() == sys.maxsize)


def test_defaults():
    unittest_setup()
    assert(_MyPyNNModelImpl.default_initial_values == {"svar": 2.0})
    assert(_MyPyNNModelImpl.default_parameters == {"param": 1.0})
    assert(_MyPyNNModelImpl.default_initial_values == {"svar": 2.0})
    assert(_MyPyNNModelImpl.default_parameters == {"param": 1.0})
