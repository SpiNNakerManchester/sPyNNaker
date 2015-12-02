from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure.\
    abstract_synapse_structure import AbstractSynapseStructure
import numpy


class SynapseStructureWeightOnly(AbstractSynapseStructure):

    def __init__(self):
        AbstractSynapseStructure.__init__(self)

    def get_n_bytes_for_connections(self, n_connections):
        return 2 * n_connections

    def get_synaptic_data(self, connections, synapse_weight_scale):
        plastic_plastic = numpy.rint(
            numpy.abs(connections["weight"]) *
            synapse_weight_scale).astype("uint32") & 0xFFFF
        return plastic_plastic.view(dtype="uint8").reshape((-1, 4))
