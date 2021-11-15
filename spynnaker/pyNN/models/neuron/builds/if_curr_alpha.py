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
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeAlpha
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class IFCurrAlpha(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an alpha-shaped current-based\
        input.

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
    :param tau_syn_E: :math:`\\tau^{syn}_e`
    :type tau_syn_E: float, iterable(float), ~pyNN.random.RandomDistribution
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
    :param exc_response: :math:`response^\\mathrm{linear}_e`
    :type exc_response: float, iterable(float),
        ~pyNN.random.RandomDistribution or (mapping) function
    :param exc_exp_response: :math:`response^\\mathrm{exponential}_e`
    :type exc_exp_response:
        float, iterable(float), ~pyNN.random.RandomDistribution or
        (mapping) function
    :param inh_response: :math:`response^\\mathrm{linear}_i`
    :type inh_response: float, iterable(float),
        ~pyNN.random.RandomDistribution or (mapping) function
    :param inh_exp_response: :math:`response^\\mathrm{exponential}_i`
    :type inh_exp_response:
        float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    """

    @default_initial_values({
        "v", "exc_response", "exc_exp_response", "inh_response",
        "inh_exp_response"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_syn_E=0.5, tau_syn_I=0.5, tau_refrac=0.1,
            i_offset=0.0, v=-65.0, exc_response=0.0, exc_exp_response=0.0,
            inh_response=0.0, inh_exp_response=0.0):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)

        synapse_type = SynapseTypeAlpha(
            exc_response, exc_exp_response, tau_syn_E, inh_response,
            inh_exp_response, tau_syn_I)

        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super().__init__(
            model_name="IF_curr_alpha", binary="IF_curr_alpha.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
