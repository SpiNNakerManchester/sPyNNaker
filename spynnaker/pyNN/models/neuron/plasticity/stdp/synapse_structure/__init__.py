from .abstract_synapse_structure import AbstractSynapseStructure
from .synapse_structure_weight_only import SynapseStructureWeightOnly
from .synapse_structure_weight_accumulator \
    import SynapseStructureWeightAccumulator
from .synapse_structure_weight_recurrent_accumulator \
    import SynapseStructureWeightRecurrentAccumulator

__all__ = [
    "AbstractSynapseStructure", "SynapseStructureWeightOnly",
    "SynapseStructureWeightAccumulator",
    "SynapseStructureWeightRecurrentAccumulator"
]
