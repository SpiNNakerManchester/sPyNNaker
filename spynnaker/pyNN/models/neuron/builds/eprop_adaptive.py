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

from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelEPropAdaptive)
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeEPropAdaptive)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeNone
from spynnaker.pyNN.models.neuron.implementations import ModelParameter


class EPropAdaptive(AbstractPyNNNeuronModelStandard):
    """ Adaptive threshold neuron with eprop support
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2",
                             "isyn_inh", "isyn_inh2", "psi", "target_rate",
                             "tau_err", "B", "small_b", "learning_signal",
                             "w_fb", "window_size",  "number_of_cues", "eta"})
    def __init__(
            self,
            # neuron model params
            tau_m: ModelParameter = 20.0, cm: ModelParameter = 1.0,
            v_rest: ModelParameter = 0, v_reset: ModelParameter = 0,
            tau_refrac: ModelParameter = 5.0, i_offset: ModelParameter = 0.0,
            v: ModelParameter = 0.0, psi: ModelParameter = 0.0,

            # synapse type params
            # tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0, tau_syn_I2=5.0,
            isyn_exc: ModelParameter = 0.0, isyn_exc2: ModelParameter = 0.0,
            isyn_inh: ModelParameter = 0.0, isyn_inh2: ModelParameter = 0.0,

            # Regularisation params
            target_rate: ModelParameter = 10.0,
            tau_err: ModelParameter = 1000.0,  # fits with 1 ms timestep

            # Threshold parameters
            B: ModelParameter = 10.0, small_b: ModelParameter = 0.0,
            small_b_0: ModelParameter = 10.0, tau_a: ModelParameter = 500.0,
            beta: ModelParameter = 1.8,

            # Learning signal and weight update constants
            learning_signal: ModelParameter = 0.0,
            w_fb: ModelParameter = 0.5,
            window_size: ModelParameter = 13000,
            number_of_cues: ModelParameter = 0,

            # eprop "global"
            eta: ModelParameter = 1.0
            ) -> None:
        """
        :param tau_m: Membrane time constant (ms)
        :param cm: Membrane capacitance (nF)
        :param v_rest: Resting membrane potential (mV)
        :param v_reset: Reset potential (mV)
        :param tau_refrac: Refractory period (ms)
        :param i_offset: Offset current (nA)
        :param v: Initial membrane potential (mV)
        :param psi: Soft threshold parameter (mV)
        :param isyn_exc: Initial excitatory synaptic current (nA)
        :param isyn_exc2: Initial excitatory synaptic current 2 (nA)
        :param isyn_inh: Initial inhibitory synaptic current (nA)
        :param isyn_inh2: Initial inhibitory synaptic current 2 (nA)
        :param target_rate: Target firing rate (Hz)
        :param tau_err: Error time constant (ms)
        :param B: Adaptive threshold parameter (mV)
        :param small_b: Adaptive threshold parameter (mV)
        :param small_b_0: Adaptive threshold parameter (mV)
        :param tau_a: Adaptive threshold time constant (ms)
        :param beta: Adaptive threshold parameter (mV)
        :param learning_signal: Learning signal (nA)
        :param w_fb: Feedback weight (nA)
        :param window_size: Window size for learning signal (ms)
        :param number_of_cues: Number of cues for learning signal
        :param eta: Learning rate
        """

        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelEPropAdaptive(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac, psi,
            # threshold params
            B, small_b, small_b_0, tau_a, beta,
            # Regularisation params
            target_rate, tau_err,
            # Learning signal params
            learning_signal, w_fb, window_size, number_of_cues,
            # eprop global
            eta)

        synapse_type = SynapseTypeEPropAdaptive(
            isyn_exc, isyn_exc2, isyn_inh, isyn_inh2)

        input_type = InputTypeCurrent()

        threshold_type = ThresholdTypeNone()

        super().__init__(
            model_name="eprop_adaptive", binary="eprop_adaptive.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)

    @classmethod
    def get_max_atoms_per_core(cls) -> int:
        """
        :return: the maximum number of atoms per core for this model.
        """
        return 8
