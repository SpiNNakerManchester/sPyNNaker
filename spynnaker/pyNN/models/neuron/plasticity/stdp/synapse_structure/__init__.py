from .abstract_synapse_structure import AbstractSynapseStructure
from .synapse_structure_weight_only import SynapseStructureWeightOnly
from .synapse_structure_weight_eligibility_trace \
    import SynapseStructureWeightEligibilityTrace

__all__ = ["AbstractSynapseStructure", "SynapseStructureWeightOnly",
           "SynapseStructureWeightEligibilityTrace"]
