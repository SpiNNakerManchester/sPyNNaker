# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeExpIzhikevichNeuromodulated)
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron.neuron_models import NeuronModelIzh

_IZK_THRESHOLD = 30.0


class IZKCurrExpIzhikevichNeuromodulation(AbstractPyNNNeuronModelStandard):
    """ Izhikevich neuron with an exponentially decaying \
        current input and neuromodulated synapses

    :param float a: :math:`a`
    :param float b: :math:`b`
    :param float c: :math:`c`
    :param float d: :math:`d`
    :param float i_offset: :math:`I_{offset}`
    :param float u: :math:`u_{init} = \\delta V_{init}`
    :param float v: :math:`v_{init} = V_{init}`
    :param float tau_syn_E: :math:`\\tau^{syn}_e`
    :param float tau_syn_I: :math:`\\tau^{syn}_i`
    :param float isyn_exc: :math:`I^{syn}_e`
    :param float isyn_inh: :math:`I^{syn}_i`
    """

    @default_initial_values({"v", "u", "isyn_exc", "isyn_inh"})
    def __init__(
            self, a=0.02, b=0.2, c=-65.0, d=2.0, i_offset=0.0, u=-14.0,
            v=-70.0, tau_syn_E=5.0, tau_syn_I=5.0, isyn_exc=0.0, isyn_inh=0.0):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelIzh(a, b, c, d, v, u, i_offset)
        synapse_type = SynapseTypeExpIzhikevichNeuromodulated(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(_IZK_THRESHOLD)

        super(IZKCurrExpIzhikevichNeuromodulation, self).__init__(
            model_name="IZK_curr_expizkneuromod",
            binary="IZK_curr_expizkneuromod.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
