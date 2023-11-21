# Copyright (c) 2020 The University of Manchester
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


class AbstractSpynnakerSplitterDelay(object, metaclass=AbstractBase):
    """
    Defines that a splitter is able to handle delays in some way.

    Ideally the splitter, and therefore the vertices it creates, are able to
    handle some delay themselves and if more is needed have the ability to
    accept spikes from a :py:class:`DelayExtensionMachineVertex`.
    """

    __slots__ = ()

    @abstractmethod
    def max_support_delay(self) -> int:
        """
        returns the max amount of delay this post vertex can support.

        :return: max delay supported in ticks
        :rtype: int
        """
        raise NotImplementedError

    def accepts_edges_from_delay_vertex(self) -> bool:
        """
        Confirms that the splitter's vertices can handle spikes coming from a
        :py:class:`DelayExtensionMachineVertex`.

        If this method returns False and the users ask for a delay larger than
        that allowed by :py:meth:`max_support_delay`, an exception will be
        raised saying a different splitter is required.

        :rtype: bool
        """
        return True
