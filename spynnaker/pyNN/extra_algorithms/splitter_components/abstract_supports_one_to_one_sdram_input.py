# Copyright (c) 2020 The University of Manchester
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
from six import add_metaclass
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractSupportsOneToOneSDRAMInput(object):
    """ An interface for a splitter that supports one-to-one input using
        SDRAM.  The splitter is assumed to handle the splitting on any inputs
        that are actually one-to-one, as it will have to create the vertices
    """

    @abstractmethod
    def handles_source_vertex(self, projection):
        """ Determine if the source vertex of the given projection is to be
            handled by the target splitter

        :param Projection projection: The projection to check the source of
        :rtype: bool
        """
