# Copyright (c) 2017 The University of Manchester
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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.machine import MachineVertex


@require_subclass(MachineVertex)
class AbstractMaxSpikes(object, metaclass=AbstractBase):
    """ Indicates a class (a \
        :py:class:`~pacman.model.graphs.machine.MachineVertex`) \
        that can describe the maximum rate that it sends spikes.

        The :py:class:`~.SynapticManager` assumes that all machine vertexes
        share the same synapse_information will have the same rates.
    """

    __slots__ = ()

    @abstractmethod
    def max_spikes_per_ts(self):
        """ Get maximum expected number of spikes per timestep

        :rtype: int
        """

    @abstractmethod
    def max_spikes_per_second(self):
        """ Get maximum expected number of spikes per second

        :param str variable: the variable to find units from
        :return: the units as a string.
        :rtype: str
        """
