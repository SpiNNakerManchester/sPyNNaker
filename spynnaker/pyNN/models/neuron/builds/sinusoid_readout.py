# Copyright (c) 2019 The University of Manchester
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

from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.neuron.implementations import ModelParameter
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFireSinusoidReadout,
)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeEPropAdaptive
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class SinusoidReadout(AbstractPyNNNeuronModelStandard):
    """ A neuron model that implements a sinusoidal readout with
        e-prop learning.
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2", "isyn_inh",
                             "isyn_inh2", "target_data", "learning_signal",
                             "w_fb", "eta", "update_ready"})
    def __init__(
            self,
            tau_m: ModelParameter = 20.0,
            cm: ModelParameter = 1.0,
            v_rest: ModelParameter = 0.0,
            v_reset: ModelParameter = 0.0,
            v_thresh: ModelParameter = 100,
            tau_refrac: ModelParameter = 0.1,
            i_offset: ModelParameter = 0.0,
            v: ModelParameter = 50,
            isyn_exc: ModelParameter = 0.0,
            isyn_exc2: ModelParameter = 0.0,
            isyn_inh: ModelParameter = 0.0,
            isyn_inh2: ModelParameter = 0.0,
            target_data: list[float] | None = None,
            # Learning signal and weight update constants
            learning_signal: ModelParameter = 0,
            w_fb: ModelParameter = 0.5,
            eta: ModelParameter = 1.0,
            update_ready: int = 1024) -> None:
        """
        :param tau_m: Membrane time constant (ms)
        :param cm: Membrane capacitance (nF)
        :param v_rest: Resting membrane potential (mV)
        :param v_reset: Reset potential (mV)
        :param v_thresh: Spike threshold (mV)
        :param tau_refrac: Refractory period (ms)
        :param i_offset: Offset current (nA)
        :param v: Initial membrane potential (mV)
        :param isyn_exc: Initial excitatory synaptic current (nA)
        :param isyn_exc2: Initial excitatory synaptic current 2 (nA)
        :param isyn_inh: Initial inhibitory synaptic current (nA)
        :param isyn_inh2: Initial inhibitory synaptic current 2 (nA)
        :param target_data: Target data for the readout (nA)
        :param learning_signal: Learning signal for e-prop (nA)
        :param w_fb: Feedback weight for the readout (nA)
        :param eta: Learning rate for e-prop
        :param update_ready: Update ready flag for e-prop
        """

        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFireSinusoidReadout(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            target_data or [0.0],
            # Learning signal params
            learning_signal, w_fb, eta, update_ready)

        synapse_type = SynapseTypeEPropAdaptive(
            isyn_exc, isyn_exc2, isyn_inh, isyn_inh2)

        input_type = InputTypeCurrent()

        threshold_type = ThresholdTypeStatic(v_thresh)

        super().__init__(
            model_name="sinusoid_readout",
            binary="sinusoid_readout.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
