from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure.\
    abstract_synapse_structure import AbstractSynapseStructure
import numpy


class SynapseStructureWeightOnly(AbstractSynapseStructure):

    def __init__(self):
        AbstractSynapseStructure.__init__(self)

    def get_n_bytes_per_connection(self):
        return 2

    def get_synaptic_data(self, connections):
        plastic_plastic = numpy.rint(
            numpy.abs(connections["weight"])).astype("uint16")
        return plastic_plastic.view(dtype="uint8").reshape((-1, 2))

    def read_synaptic_data(self, connection_indices, pp_data):
        return numpy.ravel(
            [row.view(dtype="uint16")[connection_indices] for row in pp_data])
