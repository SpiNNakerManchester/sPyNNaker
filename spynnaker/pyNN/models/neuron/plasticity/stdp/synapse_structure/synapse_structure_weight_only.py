from spinn_utilities.overrides import overrides
from .abstract_synapse_structure import AbstractSynapseStructure
import numpy


class SynapseStructureWeightOnly(AbstractSynapseStructure):
    __slots__ = ()

    @overrides(AbstractSynapseStructure.get_n_bytes_per_connection)
    def get_n_bytes_per_connection(self):
        return 2

    @overrides(AbstractSynapseStructure.get_synaptic_data)
    def get_synaptic_data(self, connections):
        plastic_plastic = numpy.rint(
            numpy.abs(connections["weight"])).astype("uint16")
        return plastic_plastic.view(dtype="uint8").reshape((-1, 2))

    @overrides(AbstractSynapseStructure.read_synaptic_data)
    def read_synaptic_data(self, fp_size, pp_data):
        return numpy.concatenate([
            pp_data[i].view(dtype="uint16")[0:fp_size[i]]
            for i in range(len(pp_data))])
