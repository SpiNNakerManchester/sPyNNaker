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
from pyNN.random import RandomDistribution
from spinn_utilities.helpful_functions import is_singleton


class ParameterHolder(object):
    """
    Holds a set of parameters and state variables to be returned in a
    PyNN-specific format.
    """

    __slots__ = (
        # A list of items of data that are to be present in each element
        "__data_items_to_return",

        # Function call to get the values
        "__get_call",

        # The merged parameters formed just before the data is read
        "__data_items",

        # A selector to use if requested
        "__selector"
    )

    def __init__(self, data_items_to_return, get_call, selector=None):
        """
        :param data_items_to_return: A list of data fields to be returned
        :type data_items_to_return: list(str) or tuple(str)
        :param get_call: A function to call to read a value
        :type get_call: callable(str, selector=None)->list
        :param selector: a description of the subrange to accept,
            or `None` for all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        """
        # pylint: disable=too-many-arguments
        self.__data_items_to_return = data_items_to_return
        self.__get_call = get_call
        self.__data_items = None
        self.__selector = selector

    def _safe_read_values(self, parameter):
        values = self.__get_call(parameter, self.__selector)

        # The values must be a single item, a list or a random distribution;
        # if a random distribution we must not have generated yet!
        if isinstance(values, RandomDistribution):
            raise ValueError(
                "Although it is possible to request the values"
                " before the simulation has run, it is not possible to read"
                " those values until after the simulation has run.  Please run"
                f" the simulation before reading {parameter}.")

        if self.__selector is not None and is_singleton(self.__selector):
            return values[0]
        return values

    def _get_data_items(self):
        """
        Merges the parameters and values in to the final data items
        """
        # If there are already merged connections cached, return those
        if self.__data_items is not None:
            return self.__data_items

        # If there is just one item to return, return the values stored
        if is_singleton(self.__data_items_to_return):
            self.__data_items = self._safe_read_values(
                self.__data_items_to_return)
            return self.__data_items

        # If there are multiple items to return, form a list
        self.__data_items = {
            param: self._safe_read_values(param)
            for param in self.__data_items_to_return}

        return self.__data_items

    def __getitem__(self, s):
        data = self._get_data_items()
        return data[s]

    def __len__(self):
        data = self._get_data_items()
        return len(data)

    def __iter__(self):
        data = self._get_data_items()
        return iter(data)

    def __str__(self):
        data = self._get_data_items()
        return data.__str__()

    def __repr__(self):
        data = self._get_data_items()
        return data.__repr__()

    def __contains__(self, item):
        data = self._get_data_items()
        return item in data

    def __getattr__(self, name):
        data = self._get_data_items()
        return getattr(data, name)

    def __eq__(self, other):
        data = self._get_data_items()
        return data == other

    def __hash__(self):
        data = self._get_data_items()
        return hash(data)

    def keys(self):
        data = self._get_data_items()
        return data.keys()

    def values(self):
        data = self._get_data_items()
        return data.items()

    def items(self):
        data = self._get_data_items()
        return data.items()
