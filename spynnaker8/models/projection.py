# Copyright (c) 2017 The University of Manchester
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

from spynnaker.pyNN.models.projection import Projection as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


# pylint: disable=abstract-method,too-many-arguments
class Projection(_BaseClass):
    """ sPyNNaker 8 projection class

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.projection.Projection` instead.
    """
    # pylint: disable=redefined-builtin
    __slots__ = [
        "__proj_label"]

    def __init__(
            self, pre_synaptic_population, post_synaptic_population,
            connector, synapse_type=None, source=None,
            receptor_type=None, space=None, label=None):
        """
        :param ~spynnaker.pyNN.models.populations.PopulationBase \
                pre_synaptic_population:
        :param ~spynnaker.pyNN.models.populations.PopulationBase \
                post_synaptic_population:
        :param AbstractConnector connector:
        :param AbstractStaticSynapseDynamics synapse_type:
        :param None source: Unsupported; must be None
        :param str receptor_type:
        :param ~pyNN.space.Space space:
        :param str label:
        """
        moved_in_v6("spynnaker8.models.projection",
                    "spynnaker.pyNN.models.projection")
        super(Projection, self).__init__(
            pre_synaptic_population, post_synaptic_population, connector,
            synapse_type, source, receptor_type, space, label)
