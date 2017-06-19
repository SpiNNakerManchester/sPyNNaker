import numpy
import math

from spinn_front_end_common.abstract_models.\
    abstract_changable_after_run import AbstractChangableAfterRun
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractPopulationSettable
from .abstract_static_synapse_dynamics import AbstractStaticSynapseDynamics
from spynnaker.pyNN import exceptions


class SynapseDynamicsStatic(
        AbstractStaticSynapseDynamics, AbstractPopulationSettable,
        AbstractChangableAfterRun):

    def __init__(self):
        AbstractStaticSynapseDynamics.__init__(self)
        AbstractPopulationSettable.__init__(self)
        AbstractChangableAfterRun.__init__(self)
        self._change_requires_mapping = True

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

    def get_n_words_for_static_connections(self, n_connections):
        return n_connections

    def get_static_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types):
        n_synapse_type_bits = int(math.ceil(math.log(n_synapse_types, 2)))

        fixed_fixed = (
            ((numpy.rint(numpy.abs(connections["weight"])).astype("uint32") &
              0xFFFF) << 16) |
            ((connections["delay"].astype("uint32") & 0xF) <<
             (8 + n_synapse_type_bits)) |
            (connections["synapse_type"].astype("uint32") << 8) |
            ((connections["target"] - post_vertex_slice.lo_atom) & 0xFF))
        fixed_fixed_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_fixed.view(dtype="uint8").reshape((-1, 4)))
        ff_size = self.get_n_items(fixed_fixed_rows, 4)
        ff_data = [fixed_row.view("uint32") for fixed_row in fixed_fixed_rows]

        return (ff_data, ff_size)

    def get_n_static_words_per_row(self, ff_size):

        # The sizes are in words, so just return them
        return ff_size

    def get_n_synapses_in_rows(self, ff_size):

        # Each word is a synapse and sizes are in words, so just return them
        return ff_size

    def read_static_synaptic_data(
            self, post_vertex_slice, n_synapse_types, ff_size, ff_data):
        n_synapse_type_bits = int(math.ceil(math.log(n_synapse_types, 2)))
        data = numpy.concatenate(ff_data)
        connections = numpy.zeros(data.size, dtype=self.NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate([numpy.repeat(
            i, ff_size[i]) for i in range(len(ff_size))])
        connections["target"] = (data & 0xFF) + post_vertex_slice.lo_atom
        connections["weight"] = (data >> 16) & 0xFFFF
        connections["delay"] = (data >> (8 + n_synapse_type_bits)) & 0xF
        connections["delay"][connections["delay"] == 0] = 16

        return connections

    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        """ True if changes that have been made require that mapping be\
            performed.  Note that this should return True the first time it\
            is called, as the vertex must require mapping as it has been\
            created!
        """
        return self._change_requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        """ Marks the point after which changes are reported.  Immediately\
            after calling this method, requires_mapping should return False.
        """
        self._change_requires_mapping = False

    @overrides(AbstractPopulationSettable.get_value)
    def get_value(self, key):
        """ Get a property
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise exceptions.InvalidParameterType(
            "Type {} does not have parameter {}".format(type(self), key))

    @overrides(AbstractPopulationSettable.set_value)
    def set_value(self, key, value):
        """ Set a property

        :param key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        """
        if hasattr(self, key):
            setattr(self, key, value)
            self._change_requires_mapping = True
        raise exceptions.InvalidParameterType(
            "Type {} does not have parameter {}".format(type(self), key))
