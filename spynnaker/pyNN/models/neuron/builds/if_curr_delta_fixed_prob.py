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

from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.input_types import InputTypeDelta
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeFixedProb
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeDelta


class IFCurrDeltaFixedProb(AbstractPyNNNeuronModelStandard):
    """
    Leaky integrate and fire neuron with an instantaneous current input, and
    fixed probability of spiking once a threshold is reached.

    :param tau_m: :math:`\\tau_m`
    :type tau_m: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param cm: :math:`C_m`
    :type cm: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param v_rest: :math:`V_{rest}`
    :type v_rest: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param v_reset: :math:`V_{reset}`
    :type v_reset: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param v_thresh: :math:`V_{thresh}`
    :type v_thresh: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param p_thresh: :math:`P_{thresh}`
    :type p_thresh: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param tau_refrac: :math:`\\tau_{refrac}`
    :type tau_refrac: float, iterable(float),
        ~spynnaker.pyNN.RandomDistribution or (mapping) function
    :param i_offset: :math:`I_{offset}`
    :type i_offset: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param v: :math:`V_{init}`
    :type v: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param isyn_exc: :math:`I^{syn}_e`
    :type isyn_exc: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param isyn_inh: :math:`I^{syn}_i`
    :type: isyn_inh: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "isyn_exc", "isyn_inh", "seed"})
    def __init__(
            self, tau_m=0.0001, cm=0.0001, v_rest=0.0, v_reset=0.0,
            v_thresh=1.0, p_thresh=1.0, tau_refrac=0.0, i_offset=0.0, v=0.0,
            isyn_exc=0.0, isyn_inh=0.0, seed=None):
        # pylint: disable=too-many-arguments
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeDelta(isyn_exc, isyn_inh)
        input_type = InputTypeDelta()
        threshold_type = ThresholdTypeFixedProb(v_thresh, p_thresh, seed)
        super().__init__(
            model_name="IF_curr_delta_fixed_prob",
            binary="IF_curr_delta_fixed_prob.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
