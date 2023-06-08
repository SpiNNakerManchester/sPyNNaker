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
    NeuronModelLeftRightReadout)
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeEPropAdaptive)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class LeftRightReadout(AbstractPyNNNeuronModelStandard):
    """
    """

    @default_initial_values({"v", "isyn_exc", "isyn_exc2", "isyn_inh",
                             "isyn_inh2",
                             "l", "w_fb", "eta", "number_of_cues"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=0.0, v_reset=0.0,
            v_thresh=100, tau_refrac=0.1, i_offset=0.0, v=50,

            isyn_exc=0.0, isyn_exc2=0.0, isyn_inh=0.0, isyn_inh2=0.0,

            rate_on=40, rate_off=0, poisson_pop_size=10,

            # Learning signal and weight update constants
            l=0, w_fb=0.5, eta=1.0, window_size=13000, number_of_cues=1):

        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeftRightReadout(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            # Learning signal params
            rate_on, rate_off, poisson_pop_size, l, w_fb, eta, window_size,
            number_of_cues)

        synapse_type = SynapseTypeEPropAdaptive(
            isyn_exc, isyn_exc2, isyn_inh, isyn_inh2)

        input_type = InputTypeCurrent()

        threshold_type = ThresholdTypeStatic(v_thresh)

        super(LeftRightReadout, self).__init__(
            model_name="left_right_readout",
            binary="left_right_readout.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
