from spynnaker.pyNN.models.neuron.synapse_structure.synapse_structure_fixed \
    import SynapseStructureFixed
from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics


class SynapseDynamicsStatic(AbstractSynapseDynamics):

    def get_synapse_structure(self):
        return SynapseStructureFixed()
