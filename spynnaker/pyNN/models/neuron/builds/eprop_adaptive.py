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


class EPropAdaptive(AbstractPyNNNeuronModelStandard):
    """ Adaptive threshold neuron with eprop support
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2",
                             "isyn_inh", "isyn_inh2",
                             "psi", "target_rate", "tau_err",
                             "B", "small_b",
                             "l", "w_fb", "window_size", "number_of_cues",
                             "eta"})
    def __init__(
            self,
            # neuron model params
            tau_m=20.0, cm=1.0, v_rest=0, v_reset=0,
            tau_refrac=5.0, i_offset=0.0, v=0.0,  psi=0.0,

            # synapse type params
            # tau_syn_E=5.0, tau_syn_E2=5.0, tau_syn_I=5.0, tau_syn_I2=5.0,
            isyn_exc=0.0, isyn_exc2=0.0, isyn_inh=0.0, isyn_inh2=0.0,

            # Regularisation params
            target_rate=10.0, tau_err=1000.0,  # fits with 1 ms timestep

            # Threshold parameters
            B=10.0, small_b=0.0, small_b_0=10.0, tau_a=500.0, beta=1.8,

            # Learning signal and weight update constants
            l=0.0, w_fb=0.5, window_size=13000, number_of_cues=0,

            # eprop "global"
            eta=1.0

            ):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelEPropAdaptive(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac, psi,
            # threshold params
            B,
            small_b,
            small_b_0,
            tau_a,
            beta,
            # Regularisation params
            target_rate, tau_err,
            # Learning signal params
            l, w_fb, window_size, number_of_cues,
            # eprop global
            eta
            )

        synapse_type = SynapseTypeEPropAdaptive(
            isyn_exc, isyn_exc2, isyn_inh, isyn_inh2)

        input_type = InputTypeCurrent()

        threshold_type = ThresholdTypeNone()

        super(EPropAdaptive, self).__init__(
            model_name="eprop_adaptive", binary="eprop_adaptive.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)

    @classmethod
    def get_max_atoms_per_core(cls):
        return 8
