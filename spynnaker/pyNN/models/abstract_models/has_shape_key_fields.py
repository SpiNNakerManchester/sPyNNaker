# Copyright (c) 2021-2023 The University of Manchester
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


class HasShapeKeyFields(object, metaclass=AbstractBase):
    """ Indicates a source that has keys in fields for each dimension of the
        source
    """

    __slots__ = []

    @abstractmethod
    def get_shape_key_fields(self, vertex_slice):
        """ Get the fields to be used for each dimension in the shape of the
            given source vertex slice, as a list of start, mask, shift values
            in the order of the fields

        :param Slice vertex_slice: The slice of the source vertex

        :rtype: list(tuple(int, int, int))
        """
