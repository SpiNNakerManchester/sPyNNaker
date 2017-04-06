from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics

from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod


@add_metaclass(AbstractBase)
class AbstractPlasticSynapseDynamics(AbstractSynapseDynamics):
    """
    AbstractPlasticSynapseDynamics : synapses which change over time
    """

    __slots__ = ()

    @abstractmethod
    def get_n_words_for_plastic_connections(self, n_connections):
        """ Get the number of 32-bit words for n_connections in a single row
        """

    @abstractmethod
    def get_plastic_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types):
        """ Get the fixed-plastic data, and plastic-plastic data for each row,\
            and lengths for the fixed_plastic and plastic-plastic parts of\
            each row.
            Data is returned as an array made up of an array of 32-bit words\
            for each row, for each of the fixed-plastic and plastic-plastic\
            data regions.  The row into which connection should go is given by\
            connection_row_indices, and the total number of rows is given by\
            n_rows.
            Lengths are returned as an array made up of an integer for each\
            row, for each of the fixed-plastic and plastic-plastic regions.
        """

    @abstractmethod
    def get_n_plastic_plastic_words_per_row(self, pp_size):
        """ Get the number of plastic plastic words to be read from each row
        """

    @abstractmethod
    def get_n_fixed_plastic_words_per_row(self, fp_size):
        """ Get the number of fixed plastic words to be read from each row
        """

    @abstractmethod
    def get_n_synapses_in_rows(self, pp_size, fp_size):
        """ Get the number of synapses in each of the rows with plastic sizes
            pp_size and fp_size
        """

    @abstractmethod
    def read_plastic_synaptic_data(
            self, post_vertex_slice, n_synapse_types, pp_size, pp_data,
            fp_size, fp_data):
        """ Read the connections indicated in the connection indices from the\
            data in pp_data and fp_data
        """
