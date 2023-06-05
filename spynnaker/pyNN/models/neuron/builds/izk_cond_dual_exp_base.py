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

    :param a: :math:`a`
    :type a: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param b: :math:`b`
    :type b: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param c: :math:`c`
    :type c: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param d: :math:`d`
    :type d: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param i_offset: :math:`I_{offset}`
    :type i_offset: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param u: :math:`u_{init} = \\delta V_{init}`
    :type u: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param v: :math:`v_{init} = V_{init}`
    :type v: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param tau_syn_E: :math:`\\tau^{syn}_e`
    :type tau_syn_E: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param tau_syn_E2: :math:`\\tau^{syn}_{e_2}`
    :type tau_syn_E2: float, iterable(float),
        ~spynnaker.pyNN.RandomDistribution or (mapping) function
    :param tau_syn_I: :math:`\\tau^{syn}_i`
    :type tau_syn_I: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param e_rev_E: :math:`E^{rev}_e`
    :type e_rev_E: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param e_rev_I: :math:`E^{rev}_i`
    :type e_rev_I: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param isyn_exc: :math:`I^{syn}_e`
    :type isyn_exc: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param isyn_exc2: :math:`I^{syn}_{e_2}`
    :type isyn_exc2: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    :param isyn_inh: :math:`I^{syn}_i`
    :type isyn_inh: float, iterable(float), ~spynnaker.pyNN.RandomDistribution
        or (mapping) function
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "u", "isyn_exc", "isyn_exc2", "isyn_inh"})
    def __init__(
            self, a=0.02, b=0.2, c=-65.0, d=2.0, i_offset=0.0, u=-14.0,
            v=-70.0, tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0, e_rev_E=0.0,
            e_rev_I=-70.0, isyn_exc=0.0, isyn_exc2=0.0, isyn_inh=0.0):
        # pylint: disable=too-many-arguments
        neuron_model = NeuronModelIzh(a, b, c, d, v, u, i_offset)
        synapse_type = SynapseTypeDualExponential(
            tau_syn_E, tau_syn_E2, tau_syn_I, isyn_exc, isyn_exc2, isyn_inh)
        input_type = InputTypeConductance(e_rev_E, e_rev_I)
        threshold_type = ThresholdTypeStatic(_IZK_THRESHOLD)

        super().__init__(
            model_name="IZK_cond_exp", binary="IZK_cond_exp_dual.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
