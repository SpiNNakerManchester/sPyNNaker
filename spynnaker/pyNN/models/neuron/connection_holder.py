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

import numpy
from numpy.lib.recfunctions import merge_arrays


class ConnectionHolder(object):
    """ Holds a set of connections to be returned in a PyNN-specific format
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
            self, data_items_to_return, as_list, n_pre_atoms, n_post_atoms,
            connections=None, fixed_values=None, notify=None):
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
            Note that if the field is to be returned, the name must also
            appear in data_items_to_return, which determines the order of
            items in the result
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
        self.__connections = connections
        self.__data_items = None
        self.__notify = notify
        self.__fixed_values = fixed_values

    def add_connections(self, connections):
        """ Add connections to the holder to be returned

        :param ~numpy.ndarray connections:
            The connection to add, as a numpy structured array of
            source, target, weight and delay
        """
        if self.__connections is None:
            self.__connections = list()
        self.__connections.append(connections)

    @property
    def connections(self):
        """ The connections stored

        :rtype: list(~numpy.ndarray)
        """
        return self.__connections

    def finish(self):
        """ Finish adding connections
        """
        if self.__notify is not None:
            self.__notify(self)

    def _get_data_items(self):
        """ Merges the connections into the result data format
        """
        # If there are already merged connections cached, return those
        if self.__data_items is not None:
            return self.__data_items

        if not self.__connections:
            # If there are no connections added, raise an exception
            if self.__connections is None:
                raise Exception(
                    "Connections are only set after run has been called, "
                    "even if you are trying to see the data before changes "
                    "have been made.  "
                    "Try examining the {} after the call to run.".format(
                        self.__data_items_to_return))
            # If the list is empty assume on a virtual machine
            # with generation on machine
            if len(self.__connections) == 0:
                raise Exception(
                    "Connections list is empty. "
                    "This may be because you are using a virtual machine. "
                    "This projection creates connections on machine.")

        # Join all the connections that have been added (probably over multiple
        # sub-vertices of a population)
        connections = numpy.concatenate(self.__connections)

        # If there are additional fixed values, merge them in
        if self.__fixed_values is not None and self.__fixed_values:
            # Generate a numpy type for the fixed values
            fixed_dtypes = [
                ('{}'.format(field[0]), None)
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
            self.__data_items = []
            for data_item in data_items:
                data_item_list = [data_item[n] for n in range(len(data_item))]
                self.__data_items.append(data_item_list)

        else:
            if self.__data_items_to_return is None:
                return []

            # Keep track of the matrices
            merged_connections = list()
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
                merged_connections.append(matrix)

            # If there is only one matrix, use it directly
            if len(merged_connections) == 1:
                self.__data_items = merged_connections[0]
            # Otherwise use a tuple of the matrices
            else:
                self.__data_items = tuple(merged_connections)

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
