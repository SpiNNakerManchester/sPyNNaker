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


class IFCondAlpha(AbstractProvidesDefaults):
    """
    Leaky integrate and fire neuron with an alpha-shaped current input.

    .. warning::
        Not currently supported by the tool chain.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "gsyn_exc", "gsyn_inh"})
    def __init__(
            self, tau_m: ModelParameter = 20, cm: ModelParameter = 1.0,
            e_rev_E: ModelParameter = 0.0, e_rev_I: ModelParameter = -70.0,
            v_rest: ModelParameter = -65.0, v_reset: ModelParameter = -65.0,
            v_thresh: ModelParameter = -50.0, tau_syn_E: ModelParameter = 0.3,
            tau_syn_I: ModelParameter = 0.5, tau_refrac: ModelParameter = 0.1,
            i_offset: ModelParameter = 0, v: ModelParameter = -65.0,
            gsyn_exc: ModelParameter = 0.0, gsyn_inh: ModelParameter = 0.0):
        # pylint: disable=unused-argument, invalid-name
        """
        :param tau_m:
        :param cm:
        :param e_rev_E:
        :param e_rev_I:
        :param v_rest:
        :param v_reset:
        :param v_thresh:
        :param tau_syn_E:
        :param tau_syn_I:
        :param tau_refrac:
        :param i_offset:
        :param v:
        :param gsyn_exc:
        :param gsyn_inh:
        """
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
