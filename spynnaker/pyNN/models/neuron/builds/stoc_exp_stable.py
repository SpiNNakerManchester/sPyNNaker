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

from typing import Optional

from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModel
from spynnaker.pyNN.models.defaults import default_parameters
from spynnaker.pyNN.models.neuron.implementations import (
    ModelParameter, NeuronImplStocExpStable)


class StocExpStable(AbstractPyNNNeuronModel):
    """ Stochastic neuron model with exponential threshold and instantaneous
        synapses, and voltage stays unless changed by input.
    """

    @default_parameters({"v_reset", "tau", "tau_refrac", "bias"})
    def __init__(
            self, v_init: ModelParameter = 0, v_reset: ModelParameter = 0,
            tau: ModelParameter = 0.1, tau_refrac: ModelParameter = 1,
            bias: ModelParameter = 0, refract_init: ModelParameter = 0,
            seed: Optional[int] = None):
        super().__init__(NeuronImplStocExpStable(
            v_init, v_reset, tau, tau_refrac, bias, refract_init, seed))
