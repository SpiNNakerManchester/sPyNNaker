# Copyright (c) 2015-2023 The University of Manchester
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

from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeSEMD
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class IFCurrExpSEMDBase(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an exponentially decaying\
        current input, where the excitatory input depends upon the inhibitory\
        input (see https://www.cit-ec.de/en/nbs/spiking-insect-vision)

    :param tau_m: :math:`\\tau_m`
    :type tau_m: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param cm: :math:`C_m`
    :type cm: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param v_rest: :math:`V_{rest}`
    :type v_rest: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param v_reset: :math:`V_{reset}`
    :type v_reset: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param v_thresh: :math:`V_{thresh}`
    :type v_thresh: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param tau_syn_E: :math:`\\tau^{syn}_{e_1}`
    :type tau_syn_E: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param tau_syn_E2: :math:`\\tau^{syn}_{e_2}`
    :type tau_syn_E2: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param tau_syn_I: :math:`\\tau^{syn}_i`
    :type tau_syn_I: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param tau_refrac: :math:`\\tau_{refrac}`
    :type tau_refrac: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param i_offset: :math:`I_{offset}`
    :type i_offset: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param v: :math:`V_{init}`
    :type v: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param isyn_exc: :math:`I^{syn}_{e_1}`
    :type isyn_exc: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param isyn_exc2: :math:`I^{syn}_{e_2}`
    :type isyn_exc2: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param isyn_inh: :math:`I^{syn}_i`
    :type isyn_inh: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param multiplicator:
    :type multiplicator:
        float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param exc2_old:
    :type exc2_old: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param scaling_factor:
    :type scaling_factor:
        float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2", "isyn_inh",
                             "exc2_old", "multiplicator"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0,
            tau_refrac=0.1, i_offset=0.0, v=-65.0, isyn_exc=0.0,
            isyn_exc2=0.0, isyn_inh=0.0, multiplicator=0.0, exc2_old=0.0,
            scaling_factor=1.0):
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeSEMD(
            tau_syn_E, tau_syn_E2, tau_syn_I, isyn_exc, isyn_exc2, isyn_inh,
            multiplicator, exc2_old, scaling_factor)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super().__init__(
            model_name="IF_curr_exp_SEMD", binary="IF_curr_exp_sEMD.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
