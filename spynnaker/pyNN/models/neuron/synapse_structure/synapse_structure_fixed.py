from spynnaker.pyNN.models.neuron.synapse_structure\
    .abstract_synapse_structure import AbstractSynapseStructure


class SynapseStructureFixed(AbstractSynapseStructure):

    def get_n_words_in_row(self, n_connections):
        return n_connections
