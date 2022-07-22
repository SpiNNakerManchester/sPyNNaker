# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from pyNN.random import RandomDistribution
from spinn_utilities.helpful_functions import is_singleton
import numpy


class ParameterHolder(object):
    """ Holds a set of parameters and state variables to be returned in a
        PyNN-specific format
    """

    __slots__ = (
        # A list of items of data that are to be present in each element
        "__data_items_to_return",

        # The vertex for which the parameters are to be retrieved
        "__vertex",

        # The merged parameters formed just before the data is read
        "__data_items",

        # A selector to use if requested
        "__selector"
    )

    def __init__(self, data_items_to_return, vertex, selector=None):
        """
        :param data_items_to_return: A list of data fields to be returned
        :type data_items_to_return: list(str) or tuple(str)
        :param AbstractPopulationSettable vertex:
            The vertex from which data can be obtained
        :param selector: a description of the subrange to accept, or None for
            all. See:
            :py:meth:`~spinn_utilities.ranged.AbstractSized.selector_to_ids`
        :type selector: None or slice or int or list(bool) or list(int)
        """
        # pylint: disable=too-many-arguments
        self.__data_items_to_return = data_items_to_return
        self.__vertex = vertex
        self.__data_items = None
        self.__selector = selector

    def _safe_read_values(self, parameter):
        if self.__selector is None:
            values = self.__vertex.get_value(parameter)
        else:
            values = self.__vertex.get_value_by_selector(
                self.__selector, parameter)

        # The values must be a single item, a list or a random distribution;
        # if a random distribution we must not have generated yet!
        if isinstance(values, RandomDistribution):
            raise ValueError(
                f"Although it is possible to request the parameter values"
                " before the simulation has run, it is not possible to read"
                " those values until after the simulation has run.  Please run"
                f" the simulation before reading {parameter}.")
        if is_singleton(values):
            return numpy.full(self.__vertex.n_atoms, values)
        return values

    def _get_data_items(self):
        """ Merges the parameters and values in to the final data items
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

    def __getattr__(self, name):
        data = self._get_data_items()
        return getattr(data, name)

    def __eq__(self, other):
        data = self._get_data_items()
        return data == other

    def __hash__(self):
        data = self._get_data_items()
        return hash(data)
