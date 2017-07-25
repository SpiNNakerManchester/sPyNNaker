from .abstract_synapse_structure import AbstractSynapseStructure
from .synapse_structure_weight_only import SynapseStructureWeightOnly
from .synapse_structure_weight_accumulator \
    import SynapseStructureWeightAccumulator

__all__ = [
    "AbstractSynapseStructure", "SynapseStructureWeightOnly",
    "SynapseStructureWeightAccumulator"
]
