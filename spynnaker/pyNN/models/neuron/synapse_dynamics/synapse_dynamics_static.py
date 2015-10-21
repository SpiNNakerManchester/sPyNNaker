import numpy

from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics \
    import AbstractSynapseDynamics


class SynapseDynamicsStatic(AbstractSynapseDynamics):

    def __init__(self):
        AbstractSynapseDynamics.__init__(self)

    def is_same_as(self, synapse_dynamics):
        return isinstance(synapse_dynamics, SynapseDynamicsStatic)

    def are_weights_signed(self):
        return False

    def get_vertex_executable_suffix(self):
        return ""

    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        return 0

    def write_parameters(self, spec, region, machine_time_step, weight_scales):
        pass

    def get_n_bytes_per_connection(self):
        return 4

    def get_synaptic_data(
            self, connections, machine_time_step, n_synapse_types,
            weight_scales):
        """ Get the fixed-fixed, fixed-plastic and plastic-plastic data for\
            the given connections.  Data is returned as an array of arrays of\
            bytes for each connection
        """
        synapse_weight_scales = numpy.array(weight_scales, dtype="float")[
            connections["synapse_type"]]

        fixed_fixed = (((numpy.rint(numpy.abs(connections["weight"]) *
                                    synapse_weight_scales).astype("uint32") &
                        0xFFFF) << 16) |
                       (numpy.rint(connections["delay"] * (1000.0 /
                                   machine_time_step)).astype("uint32") &
                        0xF << (8 + n_synapse_types)) |
                       (connections["synapse_type"] << 8) |
                       (connections["target"] & 0xFF))

        return (fixed_fixed.byteswap().view(dtype="uint8").reshape((-1, 4)),
                [numpy.zeros(0) for _ in range(connections.size)], numpy.zeros((0, 4)))
