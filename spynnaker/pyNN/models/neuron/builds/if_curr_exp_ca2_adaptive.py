# Copyright (c) 2017 The University of Manchester
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
from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.additional_inputs import (
    AdditionalInputCa2Adaptive)


class IFCurrExpCa2Adaptive(AbstractPyNNNeuronModelStandard):
    # pylint: disable=wrong-spelling-in-docstring
    """
    Model from Liu, Y. H., & Wang, X. J. (2001). Spike-frequency
    adaptation of a generalized leaky integrate-and-fire model neuron.
    *Journal of Computational Neuroscience*, 10(1), 25-45.
    `doi:10.1023/A:1008916026143
    <https://doi.org/10.1023/A:1008916026143>`_

    :param tau_m: :math:`\\tau_m`
    :param cm: :math:`C_m`
    :param v_rest: :math:`V_{rest}`
    :param v_reset: :math:`V_{reset}`
    :param v_thresh: :math:`V_{thresh}`
    :param tau_syn_E: :math:`\\tau^{syn}_e`
    :param tau_syn_I: :math:`\\tau^{syn}_i`
    :param tau_refrac: :math:`\\tau_{refrac}`
    :param i_offset: :math:`I_{offset}`
    :param tau_ca2: :math:`\\tau_{\\mathrm{Ca}^{+2}}`
    :param i_ca2: :math:`I_{\\mathrm{Ca}^{+2}}`
    :param i_alpha: :math:`\\tau_\\alpha`
    :param v: :math:`V_{init}`
    :param isyn_exc: :math:`I^{syn}_e`
    :param isyn_inh: :math:`I^{syn}_i`
    """

    @default_initial_values({"v", "isyn_exc", "isyn_inh", "i_ca2"})
    def __init__(
            self, tau_m: ModelParameter = 20.0, cm: ModelParameter = 1.0,
            v_rest: ModelParameter = -65.0, v_reset: ModelParameter = -65.0,
            v_thresh: ModelParameter = -50.0, tau_syn_E: ModelParameter = 5.0,
            tau_syn_I: ModelParameter = 5.0, tau_refrac: ModelParameter = 0.1,
            i_offset: ModelParameter = 0.0, tau_ca2: ModelParameter = 50.0,
            i_ca2: ModelParameter = 0.0, i_alpha: ModelParameter = 0.1,
            v: ModelParameter = -65.0, isyn_exc: ModelParameter = 0.0,
            isyn_inh: ModelParameter = 0.0):
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)
        additional_input_type = AdditionalInputCa2Adaptive(
            tau_ca2, i_ca2, i_alpha)

        super().__init__(
            model_name="IF_curr_exp_ca2_adaptive",
            binary="IF_curr_exp_ca2_adaptive.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type,
            additional_input_type=additional_input_type)
