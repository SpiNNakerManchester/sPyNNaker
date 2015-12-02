import numpy
import math

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

    def get_n_bytes_for_connections(self, n_connections):
        return 4 * n_connections

    def get_synaptic_data(
            self, connections, post_vertex_slice, n_synapse_types,
            weight_scales, synapse_type):
        """ Get the fixed-fixed, fixed-plastic and plastic-plastic data for\
            the given connections.  Data is returned as an array of arrays of\
            bytes for each connection
        """
        synapse_weight_scale = weight_scales[synapse_type]
        n_synapse_type_bits = int(math.ceil(math.log(n_synapse_types, 2)))

        fixed_fixed = (
            ((numpy.rint(numpy.abs(connections["weight"]) *
              synapse_weight_scale).astype("uint32") & 0xFFFF) << 16) |
            ((connections["delay"].astype("uint32") & 0xF) <<
             (8 + n_synapse_type_bits)) |
            (synapse_type << 8) |
            ((connections["target"] - post_vertex_slice.lo_atom) & 0xFF))

        return (fixed_fixed.view(dtype="uint8").reshape((-1, 4)),
                None, None)
