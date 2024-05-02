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
from typing import Iterable
from spinn_utilities.abstract_base import AbstractBase, abstractmethod


class AbstractHasParameterNames(object, metaclass=AbstractBase):
    """
    A component that has parameter names. Parameter names are usually
    properties of the component, and are frequently also settable by named
    parameter when making the component.
    """

    __slots__ = ()

    @abstractmethod
    def get_parameter_names(self) -> Iterable[str]:
        """
        Get the parameter names available from the component.

        :rtype: iterable(str)
        """
        raise NotImplementedError
