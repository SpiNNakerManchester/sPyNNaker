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

import collections
import numpy
from numpy.lib.recfunctions import merge_arrays
from numpy.typing import NDArray
from typing import (
    Callable, Iterator, List, Optional, Sequence, Tuple, Union)
from typing_extensions import TypeAlias
from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    ConnectionsArray)

_ItemType: TypeAlias = numpy.floating
_Items: TypeAlias = Union[Tuple[NDArray[_ItemType], ...], NDArray[_ItemType]]


class ConnectionHolder(object):
    """
    Holds a set of connections to be returned in a PyNN-specific format.
    """

    __slots__ = (
        # A list of items of data that are to be present in each element
        "__data_items_to_return",

        # True if the values should be returned as a list of tuples,
        # False if they should be returned as a tuple of matrices
        "__as_list",

        # The number of atoms in the pre-vertex
        "__n_pre_atoms",

        # The number of atoms in the post-vertex
        "__n_post_atoms",

        # A list of the connections that have been added
        "__connections",

        # The merged connections formed just before the data is read
        "__data_items",

        # Additional fixed values to be added to the data returned,
        # with the same values per synapse, as a list of tuples of
        # (field name, value)
        "__fixed_values",

        # A callback to call with the data when finished
        "__notify"
    )

    def __init__(
            self, data_items_to_return: Optional[Sequence[int]], as_list: bool,
            n_pre_atoms: int, n_post_atoms: int,
            connections: Optional[List[ConnectionsArray]] = None,
            fixed_values: Optional[List[Tuple[str, int]]] = None,
            notify: Optional[Callable[['ConnectionHolder'], None]] = None):
        """
        :param data_items_to_return: A list of data fields to be returned
        :type data_items_to_return: list(int) or tuple(int) or None
        :param bool as_list:
            True if the data will be returned as a list, False if it is to be
            returned as a matrix (or series of matrices)
        :param int n_pre_atoms: The number of atoms in the pre-vertex
        :param int n_post_atoms: The number of atoms in the post-vertex
        :param connections:
            Any initial connections, as a numpy structured array of
            source, target, weight and delay
        :type connections: list(~numpy.ndarray) or None
        :param fixed_values:
            A list of tuples of field names and fixed values to be appended
            to the other fields per connection, formatted as
            `[(field_name, value), ...]`.

            .. note::
                If the field is to be returned, the name must also
                appear in data_items_to_return, which determines the order of
                items in the result.
        :type fixed_values: list(tuple(str,int)) or None
        :param notify:
            A callback to call when the connections have all been added.
            This should accept a single parameter, which will contain the
            data requested
        :type notify: callable(ConnectionHolder, None) or None
        """
        # pylint: disable=too-many-arguments
        self.__data_items_to_return = data_items_to_return
        self.__as_list = as_list
        self.__n_pre_atoms = n_pre_atoms
        self.__n_post_atoms = n_post_atoms
        self.__connections: Optional[List[NDArray]] = connections
        self.__data_items: Optional[_Items] = None
        self.__notify = notify
        self.__fixed_values = fixed_values

    def add_connections(self, connections: ConnectionsArray):
        """
        Add connections to the holder to be returned.

        :param ~numpy.ndarray connections:
            The connection to add, as a numpy structured array of
            source, target, weight and delay
        """
        if self.__connections is None:
            self.__connections = list()
        self.__connections.append(connections)

    @property
    def connections(self) -> List[ConnectionsArray]:
        """
        The connections stored.

        :rtype: list(~numpy.ndarray)
        """
        return self.__connections or []

    def finish(self) -> None:
        """
        Finish adding connections.
        """
        if self.__notify is not None:
            self.__notify(self)

    def _get_data_items(self) -> _Items:
        """
        Merges the connections into the result data format.
        """
        # If there are already merged connections cached, return those
        if self.__data_items is not None:
            return self.__data_items

        if not self.__connections:
            # If there are no connections added, raise an exception
            if self.__connections is None:
                raise NotImplementedError(
                    f"Connections are only set after run has been called, "
                    f"even if you are trying to see the data before changes "
                    f"have been made. Try examining the "
                    f"{self.__data_items_to_return} after the call to run.")
            # If the list is empty assume on a virtual machine
            # with generation on machine
            if len(self.__connections) == 0:
                raise NotImplementedError(
                    "Connections list is empty. "
                    "This may be because you are using a virtual machine. "
                    "This projection creates connections on machine.")

        # Join all the connections that have been added (probably over multiple
        # sub-vertices of a population)
        connections: ConnectionsArray = numpy.concatenate(self.__connections)

        # If there are additional fixed values, merge them in
        if self.__fixed_values:
            # Generate a numpy type for the fixed values
            fixed_dtypes = [
                (f'{field[0]}', None)
                for field in self.__fixed_values]

            # Get the actual data as a record array
            fixed_data = numpy.asarray(
                tuple([field[1] for field in self.__fixed_values]),
                dtype=fixed_dtypes)

            # Tile the array to be the correct size
            fixed_values = numpy.tile(fixed_data, [len(connections), 1])

            # Add the fixed values to the connections
            connections = merge_arrays(
                (connections, fixed_values), flatten=True)

        # If we are returning a list...
        if self.__as_list:
            # ...sort by source then target
            order = numpy.lexsort(
                (connections["target"], connections["source"]))

            # There are no specific items to return, so just get
            # all the data
            if (self.__data_items_to_return is None or
                    not self.__data_items_to_return):
                data_items = connections[order]
            # There is more than one item to return, so let numpy do its magic
            elif len(self.__data_items_to_return) > 1:
                data_items = \
                    connections[order][self.__data_items_to_return]
            # There is 1 item to return, so make sure only one item exists
            else:
                data_items = \
                    connections[order][self.__data_items_to_return[0]]

            # Return in a format which can be understood by a FromListConnector
            items: List[NDArray[_ItemType]] = []
            for data_item in data_items:
                data_item_list = data_item
                if isinstance(data_item_list, collections.abc.Sequence):
                    data_item_list = list(data_item)
                items.append(data_item_list)
            self.__data_items = tuple(items)

        else:
            if self.__data_items_to_return is None:
                return ()

            # Keep track of the matrices
            merged: List[NDArray[_ItemType]] = []
            for item in self.__data_items_to_return:
                # Build an empty matrix and fill it with NAN
                matrix = numpy.empty((self.__n_pre_atoms, self.__n_post_atoms))
                matrix.fill(numpy.nan)

                # Fill in the values that have data
                # TODO: Change this to sum the items with the same
                #       (source, target) pairs
                matrix[connections["source"], connections["target"]] = \
                    connections[item]

                # Store the matrix generated
                merged.append(matrix)

            # If there is only one matrix, use it directly
            # Otherwise use a tuple of the matrices
            self.__data_items = (
                merged[0] if len(merged) == 1 else tuple(merged))

        return self.__data_items

    def __getitem__(self, s):
        data = self._get_data_items()
        return data[s]

    def __len__(self) -> int:
        data = self._get_data_items()
        return len(data)

    def __iter__(self) -> Iterator:
        data = self._get_data_items()
        return iter(data)

    def __str__(self) -> str:
        data = self._get_data_items()
        return data.__str__()

    def __repr__(self) -> str:
        data = self._get_data_items()
        return data.__repr__()

    def __getattr__(self, name):
        data = self._get_data_items()
        return getattr(data, name)
