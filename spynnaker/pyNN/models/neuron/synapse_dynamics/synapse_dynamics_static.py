# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy
from pyNN.standardmodels.synapses import StaticSynapse
from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.models.abstract_models import AbstractSettable
from .abstract_static_synapse_dynamics import AbstractStaticSynapseDynamics
from .abstract_generate_on_machine import (
    AbstractGenerateOnMachine, MatrixGeneratorID)
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.utilities.utility_calls import get_n_bits
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD


class SynapseDynamicsStatic(
        AbstractStaticSynapseDynamics, AbstractSettable,
        AbstractChangableAfterRun, AbstractGenerateOnMachine):
    """ The dynamics of a synapse that does not change over time.
    """

    __slots__ = [
        # Indicates if a change that has been made requires mapping
        "__change_requires_mapping",
        # padding to add to a synaptic row for synaptic rewiring
        "__pad_to_length",
        # weight of connections
        "__weight",
        # delay of connections
        "__delay"]

    def __init__(self, weight=StaticSynapse.default_parameters['weight'],
                 delay=None, pad_to_length=None):
        """
        :param float weight:
        :param delay: Use ``None`` to get the simulator default minimum delay.
        :type delay: float or None
        :param int pad_to_length:
        """
        self.__change_requires_mapping = True
        self.__weight = weight
        if delay is None:
            delay = get_simulator().min_delay
        self.__delay = delay
        self.__pad_to_length = pad_to_length

    @overrides(AbstractStaticSynapseDynamics.merge)
    def merge(self, synapse_dynamics):
        # We can always override a static synapse dynamics with a more
        # complex model
        return synapse_dynamics

    @overrides(AbstractStaticSynapseDynamics.is_same_as)
    def is_same_as(self, synapse_dynamics):
        return isinstance(synapse_dynamics, SynapseDynamicsStatic)

    @overrides(AbstractStaticSynapseDynamics.are_weights_signed)
    def are_weights_signed(self):
        return False

    @overrides(AbstractStaticSynapseDynamics.get_vertex_executable_suffix)
    def get_vertex_executable_suffix(self):
        return ""

    @overrides(AbstractStaticSynapseDynamics.
               get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self, n_neurons, n_synapse_types):
        return 0

    @overrides(AbstractStaticSynapseDynamics.write_parameters)
    def write_parameters(self, spec, region, weight_scales):
        # Nothing to do here
        pass

    @overrides(
        AbstractStaticSynapseDynamics.get_n_words_for_static_connections)
    def get_n_words_for_static_connections(self, n_connections):
        if (self.__pad_to_length is not None and
                n_connections < self.__pad_to_length):
            n_connections = self.__pad_to_length
        return n_connections

    @overrides(AbstractStaticSynapseDynamics.get_static_synaptic_data)
    def get_static_synaptic_data(
            self, connections, connection_row_indices, n_rows,
            post_vertex_slice, n_synapse_types, max_n_synapses):
        # pylint: disable=too-many-arguments
        n_neuron_id_bits = get_n_bits(post_vertex_slice.n_atoms)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1
        n_synapse_type_bits = get_n_bits(n_synapse_types)

        fixed_fixed = (
            ((numpy.rint(numpy.abs(connections["weight"])).astype("uint32") &
              0xFFFF) << 16) |
            ((connections["delay"].astype("uint32") & 0xF) <<
             (n_neuron_id_bits + n_synapse_type_bits)) |
            (connections["synapse_type"].astype(
                "uint32") << n_neuron_id_bits) |
            ((connections["target"] - post_vertex_slice.lo_atom) &
             neuron_id_mask))
        fixed_fixed_rows = self.convert_per_connection_data_to_rows(
            connection_row_indices, n_rows,
            fixed_fixed.view(dtype="uint8").reshape((-1, BYTES_PER_WORD)),
            max_n_synapses)
        ff_size = self.get_n_items(fixed_fixed_rows, BYTES_PER_WORD)
        if self.__pad_to_length is not None:
            # Pad the data
            fixed_fixed_rows = self._pad_row(fixed_fixed_rows, BYTES_PER_WORD)
        ff_data = [fixed_row.view("uint32") for fixed_row in fixed_fixed_rows]

        return ff_data, ff_size

    def _pad_row(self, rows, no_bytes_per_connection):
        """
        :param list(~numpy.ndarray) rows:
        :param int no_bytes_per_connection:
        :rtype: list(~numpy.ndarray)
        """
        padded_rows = []
        for row in rows:  # Row elements are (individual) bytes
            padded_rows.append(
                numpy.concatenate((
                    row, numpy.zeros(numpy.clip(
                        no_bytes_per_connection * self.__pad_to_length -
                        row.size, 0, None)).astype(
                            dtype="uint8"))).view(dtype="uint8"))

        return padded_rows

    @overrides(AbstractStaticSynapseDynamics.get_n_static_words_per_row)
    def get_n_static_words_per_row(self, ff_size):

        # The sizes are in words, so just return them
        return ff_size

    @overrides(AbstractStaticSynapseDynamics.get_n_synapses_in_rows)
    def get_n_synapses_in_rows(self, ff_size):

        # Each word is a synapse and sizes are in words, so just return them
        return ff_size

    @overrides(AbstractStaticSynapseDynamics.read_static_synaptic_data)
    def read_static_synaptic_data(
            self, post_vertex_slice, n_synapse_types, ff_size, ff_data):

        n_synapse_type_bits = get_n_bits(n_synapse_types)
        n_neuron_id_bits = get_n_bits(post_vertex_slice.n_atoms)
        neuron_id_mask = (1 << n_neuron_id_bits) - 1

        data = numpy.concatenate(ff_data)
        connections = numpy.zeros(data.size, dtype=self.NUMPY_CONNECTORS_DTYPE)
        connections["source"] = numpy.concatenate(
            [numpy.repeat(i, ff_size[i]) for i in range(len(ff_size))])
        connections["target"] = (
            (data & neuron_id_mask) + post_vertex_slice.lo_atom)
        connections["weight"] = (data >> 16) & 0xFFFF
        connections["delay"] = (data >> (n_neuron_id_bits +
                                         n_synapse_type_bits)) & 0xF
        connections["delay"][connections["delay"] == 0] = 16

        return connections

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping, extend_doc=False)
    def requires_mapping(self):
        """ True if changes that have been made require that mapping be\
            performed.  Note that this should return True the first time it\
            is called, as the vertex must require mapping as it has been\
            created!
        """
        return self.__change_requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes, extend_doc=False)
    def mark_no_changes(self):
        """ Marks the point after which changes are reported.  Immediately\
            after calling this method, requires_mapping should return False.
        """
        self.__change_requires_mapping = False

    @overrides(AbstractSettable.get_value)
    def get_value(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise InvalidParameterType(
            "Type {} does not have parameter {}".format(type(self), key))

    @overrides(AbstractSettable.set_value)
    def set_value(self, key, value):
        if hasattr(self, key):
            setattr(self, key, value)
            self.__change_requires_mapping = True
        raise InvalidParameterType(
            "Type {} does not have parameter {}".format(type(self), key))

    @overrides(AbstractStaticSynapseDynamics.get_parameter_names)
    def get_parameter_names(self):
        return ['weight', 'delay']

    @overrides(AbstractStaticSynapseDynamics.get_max_synapses)
    def get_max_synapses(self, n_words):
        return n_words

    @property
    @overrides(AbstractGenerateOnMachine.gen_matrix_id)
    def gen_matrix_id(self):
        return MatrixGeneratorID.STATIC_MATRIX.value

    @property
    @overrides(AbstractStaticSynapseDynamics.changes_during_run)
    def changes_during_run(self):
        return False

    @property
    @overrides(AbstractStaticSynapseDynamics.weight)
    def weight(self):
        return self.__weight

    @property
    @overrides(AbstractStaticSynapseDynamics.delay)
    def delay(self):
        return self.__delay

    @overrides(AbstractStaticSynapseDynamics.set_delay)
    def set_delay(self, delay):
        self.__delay = delay

    @property
    @overrides(AbstractStaticSynapseDynamics.pad_to_length)
    def pad_to_length(self):
        return self.__pad_to_length
