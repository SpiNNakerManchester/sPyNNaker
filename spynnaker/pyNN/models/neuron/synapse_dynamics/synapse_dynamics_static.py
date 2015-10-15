from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.neuron.synapse_structure.synapse_structure_fixed \
    import SynapseStructureFixed
from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics


class SynapseDynamicsStatic(AbstractSynapseDynamics):

    def __init__(self):
        AbstractSynapseDynamics.__init__(self)


    def get_maximum_delay_supported(self):
        return constants.MAX_SUPPORTED_DELAY_TICS
