from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics

from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractStaticSynapseDynamics(AbstractSynapseDynamics):
    """
    AbstractStaticSynapseDynamics: dynamics which don't change over time.
    """

    __slots__ = ()

    @abstractmethod
    def get_n_words_for_static_connections(self, n_connections):
        """ Get the number of 32-bit words for n_connections in a single row
        """

    @abstractmethod
    def get_static_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types):
        """ Get the fixed-fixed data for each row, and lengths for the\
            fixed-fixed parts of each row.
            Data is returned as an array made up of an array of 32-bit words\
            for each row for the fixed-fixed region.  The row into which\
            connection should go is given by connection_row_indices, and the\
            total number of rows is given by n_rows.
            Lengths are returned as an array made up of an integer for each\
            row, for the fixed-fixed region.
        """

    @abstractmethod
    def get_n_static_words_per_row(self, ff_size):
        """ Get the number of bytes to be read per row for the static data\
            given the size that was written to each row
        """

    @abstractmethod
    def get_n_synapses_in_rows(self, ff_size):
        """ Get the number of synapses in the rows with sizes ff_size
        """

    @abstractmethod
    def read_static_synaptic_data(
            self, post_vertex_slice, n_synapse_types, ff_size, ff_data):
        """ Read the connections from the words of data in ff_data
        """
