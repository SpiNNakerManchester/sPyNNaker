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
from spynnaker.pyNN.models.defaults import defaults, default_initial_values


@defaults
class IFFacetsConductancePopulation(object):
    """ Leaky integrate and fire neuron with conductance-based synapses and\
        fixed threshold as it is resembled by the FACETS Hardware Stage 1

    .. warning::

        Not currently supported by the tool chain.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v"})
    def __init__(
            self, g_leak=40.0, tau_syn_E=30.0, tau_syn_I=30.0, v_thresh=-55.0,
            v_rest=-65.0, e_rev_I=-80, v_reset=-80.0, v=-65.0):
        # pylint: disable=too-many-arguments, unused-argument
        raise SpynnakerException(
            "This neuron model is currently not supported by the tool chain")
