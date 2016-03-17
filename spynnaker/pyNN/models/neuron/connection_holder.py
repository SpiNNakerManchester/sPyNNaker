import numpy


class ConnectionHolder(object):
    """ Holds a set of connections to be returned in a PyNN-specific format
    """

    def __init__(
            self, data_item_to_return, as_list, n_pre_atoms, n_post_atoms,
            connections=None, filename=None):
        self._data_item_to_return = data_item_to_return
        self._as_list = as_list
        self._n_pre_atoms = n_pre_atoms
        self._n_post_atoms = n_post_atoms
        self._connections = connections
        self._merged_connections = None
        self._filename = None

    def add_connections(self, connections):
        if self._connections is None:
            self._connections = list()
        self._connections.append(connections)

    @property
    def connections(self):
        return self._connections

    def finish(self):
        if self._filename is not None:

            # TODO: Write the file
            pass

    def _merge_connections(self):
        if self._merged_connections is not None:
            return self._merged_connections

        if self._connections is None:
            raise Exception(
                "Connections are only set after run has been called, even if"
                " you are trying to see the data before changes have been"
                " made.  Try examining the weights after the call to run.")
        self._merged_connections = numpy.concatenate(self._connections)
        if self._as_list:
            order = numpy.lexsort((
                self._merged_connections["target"],
                self._merged_connections["source"]))
            if self._data_item_to_return is not None:
                self._merged_connections = self._merged_connections[order][
                    self._data_item_to_return]
            else:
                self._merged_connections = self._merged_connections[order]
        else:
            matrix = numpy.zeros((self._n_pre_atoms, self._n_post_atoms))
            matrix.fill(numpy.nan)
            matrix[
                self._merged_connections["source"],
                self._merged_connections["target"]] = self._merged_connections[
                    self._data_item_to_return]
            self._merged_connections = matrix
        return self._merged_connections

    def __getitem__(self, s):
        data = self._merge_connections()
        return data[s]

    def __len__(self):
        data = self._merge_connections()
        return len(data)

    def __iter__(self):
        data = self._merge_connections()
        return iter(data)

    def __str__(self):
        data = self._merge_connections()
        return data.__str__()

    def __repr__(self):
        data = self._merge_connections()
        return data.__repr__()

    def __getattr__(self, name):
        data = self._merge_connections()
        return getattr(data, name)
