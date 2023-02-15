# Copyright (c) 2017-2023 The University of Manchester
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
class HHCondExp(object):
    """ Single-compartment Hodgkin-Huxley model with exponentially decaying \
        current input.

    .. warning::

        Not currently supported by the tool chain.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "gsyn_exc", "gsyn_inh"})
    def __init__(
            self, gbar_K=6.0, cm=0.2, e_rev_Na=50.0, tau_syn_E=0.2,
            tau_syn_I=2.0, i_offset=0.0, g_leak=0.01, e_rev_E=0.0,
            gbar_Na=20.0, e_rev_leak=-65.0, e_rev_I=-80, e_rev_K=-90.0,
            v_offset=-63, v=-65.0, gsyn_exc=0.0, gsyn_inh=0.0):
        # pylint: disable=unused-argument
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
