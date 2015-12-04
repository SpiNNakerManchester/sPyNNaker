from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics

from abc import abstractmethod


class AbstractPlasticSynapseDynamics(AbstractSynapseDynamics):

    @abstractmethod
    def get_n_words_for_plastic_connections(self, n_connections):
        """ Get the number of 32-bit words for n_connections in a single row
        """

    @abstractmethod
    def get_plastic_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types, weight_scales, synapse_type):
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
