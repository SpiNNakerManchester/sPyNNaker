from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure \
    import AbstractSynapseStructure
import numpy


class SynapseStructureWeightRecurrentAccumulator(AbstractSynapseStructure):

    def __init__(self):
        AbstractSynapseStructure.__init__(self)

    def get_n_bytes_per_connection(self):
        return 4

    def get_synaptic_data(self, connections):
        # Plastic weight structure:
        # |      Weight     |  Accumulator   |
        # |----- 16 bit ----|---- 16 bit ----|

        accumulator_init_val = 0

        plastic_plastic = \
            numpy.rint(
                numpy.abs(connections["weight"]).astype("uint32") << 16|
                numpy.rint(accumulator_init_val).astype("uint16")
                       ).astype("uint32")

        return plastic_plastic.view(dtype="uint8").reshape((-1, 4))

    def read_synaptic_data(self, fp_size, pp_data):
        # shift by 16 to remove accumulator
        return (numpy.concatenate([
            pp_data[i][0:fp_size[i] * 4].view("uint32")
            for i in range(len(pp_data))]) >> 16) & 0xFFFF
