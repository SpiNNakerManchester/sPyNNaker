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
from spynnaker.pyNN.models.neuron.neuron_models import NeuronModelIFTrunc
from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.models.neuron.input_types import InputTypeDelta
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeDelta


class IFTruncDelta(AbstractPyNNNeuronModelStandard):
    """
    Non-leaky Integrate and fire neuron with an instantaneous current input,
    and truncation of membrane voltage so that it never goes below V_reset.

    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, tau_m: ModelParameter = 1.0, cm: ModelParameter = 1.0,
            v_reset: ModelParameter = 0.0, v_thresh: ModelParameter = 1.0,
            tau_refrac: ModelParameter = 1.0, i_offset: ModelParameter = 0.0,
            v: ModelParameter = 0.0, isyn_exc: ModelParameter = 0.0,
            isyn_inh: ModelParameter = 0.0):
        """
        :param tau_m: :math:`\\tau_m`
        :param cm: :math:`C_m`
        :param v_reset: :math:`V_{reset}`
        :param v_thresh: :math:`V_{thresh}`
        :param tau_refrac: :math:`\\tau_{refrac}`
        :param i_offset: :math:`I_{offset}`
        :param v: :math:`V_{init}`
        :param isyn_exc: :math:`I^{syn}_e`
        :param isyn_inh: :math:`I^{syn}_i`
        """
        neuron_model = NeuronModelIFTrunc(
            v, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeDelta(isyn_exc, isyn_inh)
        input_type = InputTypeDelta()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super().__init__(
            model_name="IF_trunc_delta", binary="IF_trunc_delta.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
