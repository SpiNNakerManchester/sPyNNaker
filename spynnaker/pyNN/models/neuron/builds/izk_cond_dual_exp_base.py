# Copyright (c) 2015 The University of Manchester
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

from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance
from spynnaker.pyNN.models.neuron.neuron_models import NeuronModelIzh
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeDualExponential)
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values

_IZK_THRESHOLD = 30.0


class IzkCondDualExpBase(AbstractPyNNNeuronModelStandard):
    """
    Izhikevich neuron model with conductance inputs and dual synapse.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "u", "isyn_exc", "isyn_exc2", "isyn_inh"})
    def __init__(
            self, a: ModelParameter = 0.02, b: ModelParameter = 0.2,
            c: ModelParameter = -65.0, d: ModelParameter = 2.0,
            i_offset: ModelParameter = 0.0, u: ModelParameter = -14.0,
            v: ModelParameter = -70.0, tau_syn_E: ModelParameter = 5.0,
            tau_syn_E2: ModelParameter = 5.0, tau_syn_I: ModelParameter = 5.0,
            e_rev_E: ModelParameter = 0.0, e_rev_I: ModelParameter = -70.0,
            isyn_exc: ModelParameter = 0.0, isyn_exc2: ModelParameter = 0.0,
            isyn_inh: ModelParameter = 0.0):
        """
        :param a: :math:`a`
        :param b: :math:`b`
        :param c: :math:`c`
        :param d: :math:`d`
        :param i_offset: :math:`I_{offset}`
        :param u: :math:`u_{init} = \\delta V_{init}`
        :param v: :math:`v_{init} = V_{init}`
        :param tau_syn_E: :math:`\\tau^{syn}_e`
        :param tau_syn_E2: :math:`\\tau^{syn}_{e_2}`
        :param tau_syn_I: :math:`\\tau^{syn}_i`
        :param e_rev_E: :math:`E^{rev}_e`
        :param e_rev_I: :math:`E^{rev}_i`
        :param isyn_exc: :math:`I^{syn}_e`
        :param isyn_exc2: :math:`I^{syn}_{e_2}`
        :param isyn_inh: :math:`I^{syn}_i`
        """
        neuron_model = NeuronModelIzh(a, b, c, d, v, u, i_offset)
        synapse_type = SynapseTypeDualExponential(
            tau_syn_E, tau_syn_E2, tau_syn_I, isyn_exc, isyn_exc2, isyn_inh)
        input_type = InputTypeConductance(e_rev_E, e_rev_I)
        threshold_type = ThresholdTypeStatic(_IZK_THRESHOLD)

        super().__init__(
            model_name="IZK_cond_exp_dual", binary="IZK_cond_exp_dual.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
