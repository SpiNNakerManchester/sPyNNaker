# Copyright (c) 2021 The University of Manchester
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
from pyNN.space import BaseStructure


class SupportsStructure(object, metaclass=AbstractBase):
    """
    Indicates an object that supports the setting of a PyNN structure.
    """

    @abstractmethod
    def set_structure(self, structure: BaseStructure):
        """
        Set the structure of the object.

        :param ~pynn.space.BaseStructure structure: The structure to set
        """
        raise NotImplementedError
