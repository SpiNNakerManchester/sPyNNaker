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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.require_subclass import require_subclass
from pacman.model.graphs.application import ApplicationVertex


@require_subclass(ApplicationVertex)
class AbstractHasDelayStages(object, metaclass=AbstractBase):
    """
    Indicates that this object (an application vertex) has delay stages that
    are used to increase the space required for bitfields in
    :py:func:`spynnaker.pyNN.utilities.bit_field_utilities.get_estimated_sdram_for_bit_field_region`
    """

    __slots__ = ()

    @property
    @abstractmethod
    def n_delay_stages(self):
        """
        The maximum number of delay stages required by any connection
        out of this delay extension vertex.

        :rtype: int
        """
