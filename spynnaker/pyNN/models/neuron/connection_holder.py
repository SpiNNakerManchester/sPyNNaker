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

from collections.abc import Callable, Iterator, Sequence
from typing import (
    Literal,
    TypeAlias,
    TypeGuard,
)

import numpy
from numpy.lib.recfunctions import merge_arrays
from numpy.typing import NDArray

from spinn_utilities.config_holder import get_config_bool

from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
from spynnaker.pyNN.exceptions import ConnectionHolderNotReadyException
from spynnaker.pyNN.models.neuron.synapse_dynamics.types import (
    ConnectionsArray,
)

_ItemType: TypeAlias = numpy.floating
_Items: TypeAlias = (tuple[NDArray[_ItemType], ...] | NDArray[_ItemType] |
                     tuple[list[numpy.floating], ...])


def _is_listable(value: object) -> TypeGuard[Sequence]:
    return hasattr(value, "__len__")


class ConnectionHolder:
    """
    Holds a set of connections to be returned in a PyNN-specific format.
    """

    __slots__ = (
        # True if the values should be returned as a list of tuples,
        # False if they should be returned as a tuple of matrices
        "__as_list",

        # A list of the connections that have been added
        "__connections",

        # The merged connections formed just before the data is read
        "__data_items",

        # A list of items of data that are to be present in each element
        "__data_items_to_return",

        # Additional fixed values to be added to the data returned,
        # with the same values per synapse, as a list of tuples of
        # (field name, value)
        "__fixed_values",

        # The number of atoms in the post-vertex
        "__n_post_atoms",

        # The number of atoms in the pre-vertex
        "__n_pre_atoms",

        # A callback to call with the data when finished
        "__notify"
    )

    def __init__(
            self, data_items_to_return: list[str] | None, as_list: bool,
            n_pre_atoms: int, n_post_atoms: int,
            connections: list[ConnectionsArray] | None = None,
            fixed_values: Sequence[tuple[str, float]] | None = None,
            notify: Callable[['ConnectionHolder'], None] | None = None):
        """
        :param data_items_to_return: A list of data fields to be returned
        :param as_list:
            True if the data will be returned as a list, False if it is to be
            returned as a matrix (or series of matrices)
        :param n_pre_atoms: The number of atoms in the pre-vertex
        :param n_post_atoms: The number of atoms in the post-vertex
        :param connections:
            Any initial connections, as a numpy structured array of
            source, target, weight and delay
        :param fixed_values:
            A list of tuples of field names and fixed values to be appended
            to the other fields per connection, formatted as
            `[(field_name, value), ...]`.

            .. note::
                If the field is to be returned, the name must also
                appear in data_items_to_return, which determines the order of
                items in the result.
        :param notify:
            A callback to call when the connections have all been added.
            This should accept a single parameter, which will contain the
            data requested
        """
        self.__data_items_to_return = data_items_to_return
        self.__as_list = as_list
        self.__n_pre_atoms = n_pre_atoms
        self.__n_post_atoms = n_post_atoms
        self.__connections: list[NDArray] | None = connections
        self.__data_items: _Items | None = None
        self.__notify = notify
        self.__fixed_values = fixed_values

    def add_connections(self, connections: ConnectionsArray) -> None:
        """
        Add connections to the holder to be returned.

        :param connections:
            The connection to add, as a numpy structured array of
            source, target, weight and delay
        """
        if self.__connections is None:
            self.__connections = []
        self.__connections.append(connections)
        # reset data items as there is more data
        self.__data_items = None

    @property
    def connections(self) -> list[ConnectionsArray]:
        """
        The connections stored.
        """
        return self.__connections or []

    def finish(self) -> None:
        """
        Finish adding connections.
        """
        if self.__notify is not None:
            self.__notify(self)

    def verify_data_ready(self) -> Literal[True]:
        """
        Checks the data items are ready to be used.

        Will fail if there are no connections.

        :returns: True if data is available
        :raises ConnectionHolderNotReadyException: If the data is not ready
        """
        if self.__connections:
            return True

        if get_config_bool("Machine", "virtual_board"):
            raise ConnectionHolderNotReadyException(
                "Virtual Machines never have data"
                f"{self.__data_items_to_return} likely never set.")

        if not SpynnakerDataView.is_ran_ever():
            raise ConnectionHolderNotReadyException(
                f"Connections are only set after run has been called, "
                f"even if you are trying to see the data before changes "
                f"have been made. Try examining the "
                f"{self.__data_items_to_return} after the call to run.")

        if SpynnakerDataView.get_requires_mapping():
            raise ConnectionHolderNotReadyException(
                f"Connections are only set after run using it has happened, "
                f"even if you are trying to see the data before changes "
                f"have been made. Try examining the "
                f"{self.__data_items_to_return} after the call to run.")

        if self.__connections is None:
            raise ConnectionHolderNotReadyException(
                "add_connections method never called. Despite run")

        if len(self.__connections) == 0:
            raise ConnectionHolderNotReadyException(
                "add_connections method called with empty list only.")

        raise ConnectionHolderNotReadyException(
            f"Excepted reason {self.__connections=} is False")

    def get_data_items(self) -> _Items:
        """
        Obtains the data using the connections added after run.

        :raises ConnectionHolderNotReadyException: If the data is not ready
        :returns: The raw data as if there was no ConnectionHolder
        """
        # If there are already merged connections cached, return those
        if self.__data_items is not None:
            return self.__data_items

        self.verify_data_ready()

        # Join all the connections that have been added (probably over multiple
        # sub-vertices of a population)
        connections: ConnectionsArray = numpy.concatenate(self.connections)

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
            items: list[list[numpy.floating]] = []
            # NB: The types in here are all wrong, but that's
            for data_item in data_items:
                if _is_listable(data_item):
                    items.append(list(data_item))
                else:
                    items.append(data_item)
            self.__data_items = tuple(items)

        else:
            if self.__data_items_to_return is None:
                return ()

            # Keep track of the matrices
            merged: list[NDArray[_ItemType]] = []
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

    def __getitem__(self, s: int) -> (
            numpy.floating | NDArray[numpy.floating] |
            list[numpy.floating]):
        data = self.get_data_items()
        return data[s]

    def __len__(self) -> int:
        data = self.get_data_items()
        return len(data)

    def __iter__(self) -> Iterator:
        data = self.get_data_items()
        return iter(data)

    def __str__(self) -> str:
        data = self.get_data_items()
        return data.__str__()

    def __repr__(self) -> str:
        data = self.get_data_items()
        return data.__repr__()

    def __getattr__(self, name: str) -> object:
        """
        Gets the attributes from the NDArray if applicable

        :raises AttributeError: If the data does not have this attribute.
        """
        data = self.get_data_items()
        return getattr(data, name)
