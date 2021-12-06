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
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance
from spynnaker.pyNN.models.neuron.threshold_types import (
    ThresholdTypeMaassStochastic)


class IFCondExpStoc(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with a stochastic threshold.

    Habenschuss S, Jonke Z, Maass W. Stochastic computations in cortical
    microcircuit models. *PLoS Computational Biology.* 2013;9(11):e1003311.
    `doi:10.1371/journal.pcbi.1003311
    <https://doi.org/10.1371/journal.pcbi.1003311>`_

    :param tau_m: :math:`\\tau_m`
    :param cm: :math:`C_m`
    :param v_rest: :math:`V_{rest}`
    :param v_reset: :math:`V_{reset}`
    :param v_thresh: :math:`V_{thresh}`
    :param tau_syn_E: :math:`\\tau^{syn}_e`
    :param tau_syn_I: :math:`\\tau^{syn}_i`
    :param tau_refrac: :math:`\\tau_{refrac}`
    :param i_offset: :math:`I_{offset}`
    :param e_rev_E: :math:`E^{rev}_e`
    :param e_rev_I: :math:`E^{rev}_i`
    :param du_th: :math:`du_{thresh}`
    :param tau_th: :math:`\\tau_{thresh}`
    :param v: :math:`V_{init}`
    :param isyn_exc: :math:`I^{syn}_e`
    :param isyn_inh: :math:`I^{syn}_i`
    :type tau_m: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type cm: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type v_rest: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type v_reset: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type v_thresh: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type tau_syn_E: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type tau_syn_I: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type tau_refrac: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type i_offset: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type e_rev_E: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type e_rev_I: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type du_th: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type tau_th: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type v: Float, float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type isyn_exc: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :type isyn_inh: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    """

    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_syn_E=5.0, tau_syn_I=5.0, tau_refrac=0.1,
            i_offset=0.0, e_rev_E=0.0, e_rev_I=-70.0, du_th=0.5, tau_th=20.0,
            v=-65.0, isyn_exc=0.0, isyn_inh=0.0):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeConductance(e_rev_E, e_rev_I)
        threshold_type = ThresholdTypeMaassStochastic(
            du_th, tau_th, v_thresh)

        super().__init__(
            model_name="IF_cond_exp_stoc", binary="IF_cond_exp_stoc.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
