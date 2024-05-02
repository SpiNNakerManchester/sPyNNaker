# Copyright (c) 2024 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModel
from spynnaker.pyNN.models.defaults import default_parameters
from spynnaker.pyNN.models.neuron.implementations import NeuronImplStocExp


class StocExp(AbstractPyNNNeuronModel):
    """ Stochastic neuron model exponential threshold and instantaneous
        synapses, and voltage which is reset each time step.
    """

    @default_parameters({"tau", "bias"})
    def __init__(self, tau=10, bias=0, refract_init=0, seed=None):
        super().__init__(NeuronImplStocExp(tau, bias, refract_init, seed))
