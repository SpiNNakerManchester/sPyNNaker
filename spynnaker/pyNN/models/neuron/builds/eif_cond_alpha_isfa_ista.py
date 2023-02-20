# Copyright (c) 2015 The University of Manchester
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

from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.defaults import defaults, default_initial_values


@defaults
class EIFConductanceAlphaPopulation(object):
    """ Exponential integrate and fire neuron with spike triggered and \
        sub-threshold adaptation currents (isfa, ista reps.)

    .. warning::

        Not currently supported by the tool chain.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "w", "gsyn_exc", "gsyn_inh"})
    def __init__(self, tau_m=9.3667, cm=0.281, v_rest=-70.6,
                 v_reset=-70.6, v_thresh=-50.4, tau_syn_E=5.0, tau_syn_I=0.5,
                 tau_refrac=0.1, i_offset=0.0, a=4.0, b=0.0805, v_spike=-40.0,
                 tau_w=144.0, e_rev_E=0.0, e_rev_I=-80.0, delta_T=2.0,
                 v=-70.6, w=0.0, gsyn_exc=0.0, gsyn_inh=0.0):
        # pylint: disable=too-many-arguments, unused-argument
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
