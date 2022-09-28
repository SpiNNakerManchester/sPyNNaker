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

import pytest
import sys
from spinn_utilities.classproperty import classproperty
from spynnaker.pyNN.config_setup import unittest_setup
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.models.neuron.abstract_pynn_neuron_model import (
    AbstractPyNNNeuronModel)
from spynnaker.pyNN.models.defaults import default_initial_values, defaults
from spynnaker.pyNN.exceptions import SpynnakerException


@defaults
class _MyPyNNModelImpl(AbstractPyNNModel):

    default_population_parameters = {}

    @default_initial_values({"svar"})
    def __init__(self, param=1.0, svar=2.0):
        pass

    @classproperty
    def absolute_max_atoms_per_core(cls):  # @NoSelf
        return 1000

    def create_vertex(self, n_neurons, label):
        return None


class _MyNeuronModelImpl(AbstractPyNNNeuronModel):
    pass


class _MyOtherNeuronModel(_MyNeuronModelImpl):
    pass


def test_max_atoms_per_core():
    unittest_setup()
    with pytest.raises(SpynnakerException):
        _MyPyNNModelImpl.set_model_max_atoms_per_dimension_per_core(2000)
    _MyPyNNModelImpl.set_model_max_atoms_per_dimension_per_core(100)
    _MyNeuronModelImpl.set_model_max_atoms_per_dimension_per_core(20)
    _MyOtherNeuronModel.set_model_max_atoms_per_dimension_per_core(50)
    assert _MyPyNNModelImpl.get_model_max_atoms_per_dimension_per_core() == 100
    assert (
        _MyNeuronModelImpl.get_model_max_atoms_per_dimension_per_core() == 20)
    assert (
        _MyOtherNeuronModel.get_model_max_atoms_per_dimension_per_core() == 50)

    _MyPyNNModelImpl.set_model_max_atoms_per_dimension_per_core((20, 20))
    assert (
        _MyPyNNModelImpl.get_model_max_atoms_per_dimension_per_core() ==
        (20, 20))
    with pytest.raises(SpynnakerException):
        _MyPyNNModelImpl.set_model_max_atoms_per_dimension_per_core((100, 100))


def test_reset_max_atoms_per_core():
    unittest_setup()
    _MyNeuronModelImpl.set_model_max_atoms_per_dimension_per_core(20)
    _MyNeuronModelImpl.set_model_max_atoms_per_dimension_per_core()
    _MyPyNNModelImpl.set_model_max_atoms_per_dimension_per_core(100)
    _MyPyNNModelImpl.set_model_max_atoms_per_dimension_per_core()
    assert (_MyNeuronModelImpl.get_model_max_atoms_per_dimension_per_core() ==
            sys.maxsize)
    assert (_MyPyNNModelImpl.get_model_max_atoms_per_dimension_per_core() ==
            1000)


def test_defaults():
    unittest_setup()
    assert _MyPyNNModelImpl.default_initial_values == {"svar": 2.0}
    assert _MyPyNNModelImpl.default_parameters == {"param": 1.0}
    assert _MyPyNNModelImpl.default_initial_values == {"svar": 2.0}
    assert _MyPyNNModelImpl.default_parameters == {"param": 1.0}
