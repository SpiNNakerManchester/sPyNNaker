# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
