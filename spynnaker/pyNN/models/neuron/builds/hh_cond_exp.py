# Copyright (c) 2015 The University of Manchester
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

from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.defaults import (
    AbstractProvidesDefaults, default_initial_values)
from spynnaker.pyNN.models.neuron.implementations import ModelParameter


class HHCondExp(AbstractProvidesDefaults):
    """
    Single-compartment Hodgkin-Huxley model with exponentially decaying
    current input.

    .. warning::
        Not currently supported by the tool chain.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "gsyn_exc", "gsyn_inh"})
    def __init__(
            self, gbar_K: ModelParameter = 6.0, cm: ModelParameter = 0.2,
            e_rev_Na: ModelParameter = 50.0, tau_syn_E: ModelParameter = 0.2,
            tau_syn_I: ModelParameter = 2.0, i_offset: ModelParameter = 0.0,
            g_leak: ModelParameter = 0.01, e_rev_E: ModelParameter = 0.0,
            gbar_Na: ModelParameter = 20.0, e_rev_leak: ModelParameter = -65.0,
            e_rev_I: ModelParameter = -80, e_rev_K: ModelParameter = -90.0,
            v_offset: ModelParameter = -63, v: ModelParameter = -65.0,
            gsyn_exc: ModelParameter = 0.0, gsyn_inh: ModelParameter = 0.0):
        # pylint: disable=unused-argument,invalid-name
        """
        :param gbar_K:
        :param cm:
        :param e_rev_Na:
        :param tau_syn_E:
        :param tau_syn_I:
        :param i_offset:
        :param g_leak:
        :param e_rev_E:
        :param gbar_Na:
        :param e_rev_leak:
        :param e_rev_I:
        :param e_rev_K:
        :param v_offset:
        :param v:
        :param gsyn_exc:
        :param gsyn_inh:
        """
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
