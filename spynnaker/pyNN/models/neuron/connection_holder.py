import numpy
from numpy.lib.recfunctions import merge_arrays


class ConnectionHolder(object):
    """ Holds a set of connections to be returned in a PyNN-specific format
    """

    __slots__ = (

        # A list of items of data that are to be present in each element
        "_data_items_to_return",

        # True if the values should be returned as a list of tuples,
        # False if they should be returned as a tuple of matrices
        "_as_list",

        # The number of atoms in the pre-vertex
        "_n_pre_atoms",

        # The number of atoms in the post-vertex
        "_n_post_atoms",

        # A list of the connections that have been added
        "_connections",

        # The merged connections formed just before the data is read
        "_data_items",

        # Additional fixed values to be added to the data returned,
        # with the same values per synapse, as a list of tuples of
        # (field name, value)
        "_fixed_values",

        # A callback to call with the data when finished
        "_notify",
    )

    def __init__(
            self, data_items_to_return, as_list, n_pre_atoms, n_post_atoms,
            connections=None, fixed_values=None, notify=None):
        """

        :param data_items_to_return: A list of data fields to be returned
        :param as_list:\
            True if the data will be returned as a list, False if it is to be\
            returned as a matrix (or series of matrices)
        :param n_pre_atoms: The number of atoms in the pre-vertex
        :param n_post_atoms: The number of atoms in the post-vertex
        :param connections:\
            Any initial connections, as a numpy structured array of\
            source, target, weight and delay
        :param fixed_values:\
            A list of tuples of field names and fixed values to be appended\
            to the other fields per connection, formatted as\
            [(field_name, value), ...].
            Note that if the field is to be returned, the name must also\
            appear in data_items_to_return, which determines the order of\
            items in the result
        :param notify:\
            A callback to call when the connections have all been added.\
            This should accept a single parameter, which will contain the\
            data requested
        """
        self._data_items_to_return = data_items_to_return
        self._as_list = as_list
        self._n_pre_atoms = n_pre_atoms
        self._n_post_atoms = n_post_atoms
        self._connections = connections
        self._data_items = None
        self._notify = notify
        self._fixed_values = fixed_values

    def add_connections(self, connections):
        """ Add connections to the holder to be returned

        :param connections:\
            The connection to add, as a numpy structured array of\
            source, target, weight and delay
        """
        if self._connections is None:
            self._connections = list()
        self._connections.append(connections)

    @property
    def connections(self):
        """ The connections stored
        """
        return self._connections

    def finish(self):
        """ Finish adding connections
        """
        if self._notify is not None:
            self._notify(self)

    def _get_data_items(self):
        """ Merges the connections into the result data format
        """

        # If there are already merged connections cached, return those
        if self._data_items is not None:
            return self._data_items

        # If there are no connections added, raise an exception
        if self._connections is None:
            raise Exception(
                "Connections are only set after run has been called, even if"
                " you are trying to see the data before changes have been"
                " made.  Try examining the {} after the call to run.".format(
                    self._data_items_to_return))

        # Join all the connections that have been added (probably over multiple
        # sub-vertices of a population)
        connections = numpy.concatenate(self._connections)

        # If there are additional fixed values, merge them in
        if self._fixed_values is not None and len(self._fixed_values) > 0:

            # Generate a numpy type for the fixed values
            fixed_dtypes = [
                ('{}'.format(field[0]), None)
                for field in self._fixed_values]

            # Get the actual data as a record array
            fixed_data = numpy.asarray(
                tuple([field[1] for field in self._fixed_values]),
                dtype=fixed_dtypes)

            # Tile the array to be the correct size
            fixed_values = numpy.tile(fixed_data, [len(connections), 1])

            # Add the fixed values to the connections
            connections = merge_arrays(
                (connections, fixed_values), flatten=True)

        # If we are returning a list...
        if self._as_list:

            # ...sort by source then target
            order = numpy.lexsort(
                (connections["target"], connections["source"]))

            # There are no specific items to return, so just get
            # all the data
            if (self._data_items_to_return is None or
                    len(self._data_items_to_return) == 0):
                self._data_items = connections[order]

            # There is more than one item to return, so let numpy do its magic
            elif len(self._data_items_to_return) > 1:
                self._data_items = \
                    connections[order][self._data_items_to_return]

            # There is 1 item to return, so make sure only one item exists
            else:
                self._data_items = \
                    connections[order][self._data_items_to_return[0]]

        else:

            if self._data_items_to_return is None:
                return []

            # Keep track of the matrices
            merged_connections = list()
            for item in self._data_items_to_return:

                # Build an empty matrix and fill it with NAN
                matrix = numpy.empty((self._n_pre_atoms, self._n_post_atoms))
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
                self._data_items = merged_connections[0]

            # Otherwise use a tuple of the matrices
            else:
                self._data_items = tuple(merged_connections)

        return self._data_items

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
