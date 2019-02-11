from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    AbstractSynapseStructure)


class SynapseStructureWeightAccumulator(AbstractSynapseStructure):
    __slots__ = ()

    @overrides(AbstractSynapseStructure.get_n_half_words_per_connection)
    def get_n_half_words_per_connection(self):
        return 2

    @overrides(AbstractSynapseStructure.get_weight_half_word)
    def get_weight_half_word(self):
        return 0
