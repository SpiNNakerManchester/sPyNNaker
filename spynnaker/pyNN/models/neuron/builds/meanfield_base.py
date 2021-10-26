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

from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance
from spynnaker.pyNN.models.neuron.neuron_models import MeanfieldModelEitn
from spynnaker.pyNN.models.neuron.neuron_models import Config
from spynnaker.pyNN.models.neuron.neuron_models import Mathsbox
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponential
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic
from spynnaker.pyNN.models.neuron import AbstractPyNNMeanfieldModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values

_IZK_THRESHOLD = 30.0


class MeanfieldBase(AbstractPyNNMeanfieldModelStandard):
    """ Izhikevich neuron model with conductance inputs.

    :param a: :math:`a`
    :type a: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param b: :math:`b`
    :type b: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param c: :math:`c`
    :type c: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param d: :math:`d`
    :type d: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param i_offset: :math:`I_{offset}`
    :type i_offset: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param u: :math:`u_{init} = \\delta V_{init}`
    :type u: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param v: :math:`v_{init} = V_{init}`
    :type v: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param tau_syn_E: :math:`\\tau^{syn}_e`
    :type tau_syn_E: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param tau_syn_I: :math:`\\tau^{syn}_i`
    :type tau_syn_I: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param e_rev_E: :math:`E^{rev}_e`
    :type e_rev_E: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param e_rev_I: :math:`E^{rev}_i`
    :type e_rev_I: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param isyn_exc: :math:`I^{syn}_e`
    :type isyn_exc: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    :param isyn_inh: :math:`I^{syn}_i`
    :type isyn_inh: float, iterable(float), ~pyNN.random.RandomDistribution
        or (mapping) function
    """

    # noinspection PyPep8Naming
    @default_initial_values({"Ve", "Vi", "muV", "sV", "muGn", "TvN", "Vthre",
                             "Fout_th", "err_func", "isyn_exc", "isyn_inh"})
    def __init__(self,
                 nbr=1,
                 a=0,
                 b=0,
                 tauw=1.,
                 Trefrac=5.0,
                 Vreset=-65.,
                 delta_v=-0.5,
                 ampnoise=0.0,
                 Timescale_inv=0.5,
                 Ve=9.,
                 Vi=23.,

                 pconnec=0.05,
                 q_exc=1.5,
                 q_inh=5.0,
                 Tsyn_exc=5.,
                 Tsyn_inh=5.,
                 Erev_exc=0.,
                 Erev_inh=-80.,
                 Ntot=10000,
                 gei=0.2,
                 ext_drive=2.5,
                 afferent_exc_fraction=1.,

                 Gl=10.,
                 Cm=200.,
                 El=-70.,

                 p0=-0.0515518,
                 p1=0.00455197,
                 p2=-0.00760625,
                 p3=0.00094851,
                 p4=0.001,
                 p5=-0.0009863,
                 p6=-0.0026474,
                 p7=-0.0135417,
                 p8=0.0028742,
                 p9=0.0029213,
                 p10=-0.014084,

                 muV=0.,
                 muV0=-0.06,
                 DmuV0=0.01,

                 sV=0.,
                 sV0=0.004,
                 DsV0=0.006,

                 muGn=0.,

                 TvN=0.,
                 TvN0=0.5,
                 DTvN0=1.,

                 Vthre=-50.,
                 Fout_th=0.,

                 tau_syn_E=5.0,
                 tau_syn_I=5.0,
                 e_rev_E=0.0,
                 e_rev_I=-70.0,

                 isyn_exc=0.0,
                 isyn_inh=0.0,

                 sample=100,
                 err_func=0.):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = MeanfieldModelEitn(nbr, a, b, tauw, Trefrac,
                                          Vreset, delta_v, ampnoise,
                                          Timescale_inv, Ve, Vi)
        config = Config(pconnec, q_exc, q_inh,
                        Tsyn_exc, Tsyn_inh,
                        Erev_exc, Erev_inh,
                        Ntot, gei, ext_drive,
                        afferent_exc_fraction,
                        Gl, Cm, El,
                        muV, muV0,DmuV0,
                        sV, sV0, DsV0,
                        muGn,
                        TvN, TvN0, DTvN0,
                        Vthre, Fout_th)
        Vthre_params_Ve = 
        Vthre_params_vi = 
        mathsbox = Mathsbox(sample, err_func)
        synapse_type = SynapseTypeExponential(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeConductance(e_rev_E, e_rev_I)
        threshold_type = ThresholdTypeStatic(_IZK_THRESHOLD)

        super().__init__(
            model_name="meanfield_model_cond",
            binary="meanfield_model_cond.aplx",
            neuron_model=neuron_model,
            config=config,
            Vthre_params_Ve = , #PUT HERE
            Vthre_params_vi = , #PUT HERE
            mathsbox=mathsbox,
            input_type=input_type,
            synapse_type=synapse_type,
            threshold_type=threshold_type)
