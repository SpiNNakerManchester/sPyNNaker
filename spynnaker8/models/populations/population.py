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

from spynnaker.pyNN.models.populations import Population as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


# pylint: disable=abstract-method
class Population(_BaseClass):
    """
    PyNN 0.9 population object.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.populations.Population` instead.
    """

    def __init__(
            self, size, cellclass, cellparams=None, structure=None,
            initial_values=None, label=None, additional_parameters=None):
        """
        :param int size: The number of neurons in the population
        :param cellclass: The implementation of the individual neurons.
        :type cellclass: type or AbstractPyNNModel
        :param cellparams: Parameters to pass to ``cellclass`` if it
            is a class to instantiate. Must be ``None`` if ``cellclass`` is an
            instantiated object.
        :type cellparams: dict(str,object) or None
        :param ~pyNN.space.BaseStructure structure:
        :param dict(str,float) initial_values:
            Initial values of state variables
        :param str label: A label for the population
        :param additional_parameters:
            Additional parameters to pass to the vertex creation function.
        :type additional_parameters: dict(str, ...)
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.populations.Population",
                    "spynnaker.pyNN.models.populations.Population")
        super().__init__(
            size, cellclass, cellparams, structure, initial_values, label,
            additional_parameters)
