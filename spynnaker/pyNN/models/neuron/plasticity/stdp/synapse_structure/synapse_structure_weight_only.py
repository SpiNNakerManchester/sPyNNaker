from spinn_utilities.overrides import overrides
from .abstract_synapse_structure import AbstractSynapseStructure


class SynapseStructureWeightOnly(AbstractSynapseStructure):
    __slots__ = ()

    @overrides(AbstractSynapseStructure.get_n_half_words_per_connection)
    def get_n_half_words_per_connection(self):
        return 1

    @overrides(AbstractSynapseStructure.get_weight_half_word)
    def get_weight_half_word(self):
        return 0
