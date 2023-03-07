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

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)


class AbstractInputType(
        AbstractStandardNeuronComponent, metaclass=AbstractBase):
    """ Represents a possible input type for a neuron model (e.g., current).
    """
    __slots__ = ()

    @abstractmethod
    def get_global_weight_scale(self):
        """ Get the global weight scaling value.

        :return: The global weight scaling value
        :rtype: float
        """
