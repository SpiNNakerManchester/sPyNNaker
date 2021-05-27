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

import logging
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from spinn_utilities.config_holder import get_config_int
from spinn_front_end_common.abstract_models import (
    AbstractChangableAfterRun, AbstractProvidesOutgoingPartitionConstraints,
    AbstractCanReset, AbstractRewritesDataSpecification)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl, TDMAAwareApplicationVertex)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, AbstractNeuronRecordable, NeuronRecorder)
from spynnaker.pyNN.models.abstract_models import (
    AbstractPopulationInitializable, AbstractAcceptsIncomingSynapses,
    AbstractPopulationSettable, AbstractContainsUnits)
from spynnaker.pyNN.exceptions import InvalidParameterType
from spynnaker.pyNN.utilities.ranged import (
    SpynnakerRangeDictionary)
from .synaptic_manager import SynapticManager

# TODO: Make sure these values are correct (particularly CPU cycles)
_NEURON_BASE_DTCM_USAGE_IN_BYTES = 9 * BYTES_PER_WORD
_NEURON_BASE_N_CPU_CYCLES_PER_NEURON = 22
_NEURON_BASE_N_CPU_CYCLES = 10

logger = FormatAdapter(logging.getLogger(__name__))


class AbstractPopulationVertex(
        TDMAAwareApplicationVertex, AbstractContainsUnits,
        AbstractSpikeRecordable, AbstractNeuronRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractPopulationInitializable, AbstractPopulationSettable,
        AbstractChangableAfterRun, AbstractAcceptsIncomingSynapses,
        ProvidesKeyToAtomMappingImpl, AbstractCanReset):
    """ Underlying vertex model for Neural Populations.\
        Not actually abstract.
    """

    __slots__ = [
        "__change_requires_mapping",
        "__change_requires_data_generation",
        "__incoming_spike_buffer_size",
        "__n_atoms",
        "__n_profile_samples",
        "__neuron_impl",
        "__neuron_recorder",
        "_parameters",  # See AbstractPyNNModel
        "__pynn_model",
        "_state_variables",  # See AbstractPyNNModel
        "__synapse_manager",
        "__time_between_requests",
        "__units",
        "__n_data_specs",
        "__initial_state_variables",
        "__has_run"]

    #: recording region IDs
    _SPIKE_RECORDING_REGION = 0

    #: the size of the runtime SDP port data region
    _RUNTIME_SDP_PORT_SIZE = BYTES_PER_WORD

    #: The Buffer traffic type
    _TRAFFIC_IDENTIFIER = "BufferTraffic"

    # 5 elements before the start of global parameters
    # 1. has key, 2. key, 3. n atoms,
    # 4. n synapse types, 5. incoming spike buffer size.
    BYTES_TILL_START_OF_GLOBAL_PARAMETERS = 5 * BYTES_PER_WORD

    def __init__(
            self, n_neurons, label, constraints, max_atoms_per_core,
            spikes_per_second, ring_buffer_sigma, incoming_spike_buffer_size,
            neuron_impl, pynn_model, drop_late_spikes, splitter):
        """
        :param int n_neurons: The number of neurons in the population
        :param str label: The label on the population
        :param list(~pacman.model.constraints.AbstractConstraint) constraints:
            Constraints on where a population's vertices may be placed.
        :param int max_atoms_per_core:
            The maximum number of atoms (neurons) per SpiNNaker core.
        :param spikes_per_second: Expected spike rate
        :type spikes_per_second: float or None
        :param ring_buffer_sigma:
            How many SD above the mean to go for upper bound of ring buffer
            size; a good starting choice is 5.0. Given length of simulation
            we can set this for approximate number of saturation events.
        :type ring_buffer_sigma: float or None
        :param incoming_spike_buffer_size:
        :type incoming_spike_buffer_size: int or None
        :param bool drop_late_spikes: control flag for dropping late packets.
        :param AbstractNeuronImpl neuron_impl:
            The (Python side of the) implementation of the neurons themselves.
        :param AbstractPyNNNeuronModel pynn_model:
            The PyNN neuron model that this vertex is working on behalf of.
        :param splitter: splitter object
        :type splitter: None or
            ~pacman.model.partitioner_splitters.abstract_splitters.AbstractSplitterCommon
        """

        # pylint: disable=too-many-arguments, too-many-locals
        super().__init__(label, constraints, max_atoms_per_core, splitter)

        self.__n_atoms = self.round_n_atoms(n_neurons, "n_neurons")
        self.__n_data_specs = 0

        # buffer data
        self.__incoming_spike_buffer_size = incoming_spike_buffer_size

        if incoming_spike_buffer_size is None:
            self.__incoming_spike_buffer_size = get_config_int(
                "Simulation", "incoming_spike_buffer_size")

        self.__neuron_impl = neuron_impl
        self.__pynn_model = pynn_model
        self._parameters = SpynnakerRangeDictionary(n_neurons)
        self.__neuron_impl.add_parameters(self._parameters)
        self.__initial_state_variables = SpynnakerRangeDictionary(n_neurons)
        self.__neuron_impl.add_state_variables(self.__initial_state_variables)
        self._state_variables = self.__initial_state_variables.copy()

        # Set up for recording
        recordable_variables = list(
            self.__neuron_impl.get_recordable_variables())
        record_data_types = dict(
            self.__neuron_impl.get_recordable_data_types())
        self.__neuron_recorder = NeuronRecorder(
            recordable_variables, record_data_types, [NeuronRecorder.SPIKES],
            n_neurons, [NeuronRecorder.PACKETS],
            {NeuronRecorder.PACKETS: NeuronRecorder.PACKETS_TYPE})

        # Set up synapse handling
        self.__synapse_manager = SynapticManager(
            self.__neuron_impl.get_n_synapse_types(), ring_buffer_sigma,
            spikes_per_second, drop_late_spikes)

        # bool for if state has changed.
        self.__change_requires_mapping = True
        self.__change_requires_data_generation = False
        self.__has_run = False

        # Set up for profiling
        self.__n_profile_samples = get_config_int(
            "Reports", "n_profile_samples")

    @overrides(AbstractNeuronRecordable.get_expected_n_rows)
    def get_expected_n_rows(
            self, n_machine_time_steps, sampling_rate, vertex, variable):
        return self.__neuron_recorder.expected_rows_for_a_run_time(
            n_machine_time_steps, sampling_rate)

    @property
    @overrides(TDMAAwareApplicationVertex.n_atoms)
    def n_atoms(self):
        return self.__n_atoms

    @property
    def incoming_spike_buffer_size(self):
        return self.__incoming_spike_buffer_size

    @property
    def parameters(self):
        return self._parameters

    @property
    def state_variables(self):
        return self._state_variables

    @property
    def neuron_impl(self):
        return self.__neuron_impl

    @property
    def n_profile_samples(self):
        return self.__n_profile_samples

    @property
    def neuron_recorder(self):
        return self.__neuron_recorder

    @property
    def synapse_manager(self):
        return self.__synapse_manager

    def set_has_run(self):
        """ Set the flag has run so initialize only affects state variables

        :rtype: None
        """
        self.__has_run = True

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__change_requires_mapping

    @property
    @overrides(AbstractChangableAfterRun.requires_data_generation)
    def requires_data_generation(self):
        return self.__change_requires_data_generation

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        # If mapping will happen, reset things that need this
        if self.__change_requires_mapping:
            self.__synapse_manager.clear_all_caches()
        self.__change_requires_mapping = False
        self.__change_requires_data_generation = False

    def get_sdram_usage_for_neuron_params(self, vertex_slice):
        """ Calculate the SDRAM usage for just the neuron parameters region.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the slice of atoms.
        :return: The SDRAM required for the neuron region
        """
        return (
            self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS +
            self.tdma_sdram_size_in_bytes +
            self.__neuron_impl.get_sdram_usage_in_bytes(vertex_slice.n_atoms))

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__neuron_recorder.is_recording(NeuronRecorder.SPIKES)

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        self.set_recording(
            NeuronRecorder.SPIKES, new_state, sampling_interval, indexes)

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, buffer_manager, machine_time_step):
        return self.__neuron_recorder.get_spikes(
            self.label, buffer_manager, placements, self,
            NeuronRecorder.SPIKES, machine_time_step)

    @overrides(AbstractNeuronRecordable.get_recordable_variables)
    def get_recordable_variables(self):
        return self.__neuron_recorder.get_recordable_variables()

    @overrides(AbstractNeuronRecordable.is_recording)
    def is_recording(self, variable):
        return self.__neuron_recorder.is_recording(variable)

    @overrides(AbstractNeuronRecordable.set_recording)
    def set_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        self.__change_requires_mapping = not self.is_recording(variable)
        self.__neuron_recorder.set_recording(
            variable, new_state, sampling_interval, indexes)

    @overrides(AbstractNeuronRecordable.get_data)
    def get_data(self, variable, n_machine_time_steps, placements,
                 buffer_manager, machine_time_step):
        # pylint: disable=too-many-arguments
        return self.__neuron_recorder.get_matrix_data(
            self.label, buffer_manager, placements, self, variable,
            n_machine_time_steps)

    @overrides(AbstractNeuronRecordable.get_neuron_sampling_interval)
    def get_neuron_sampling_interval(self, variable):
        return self.__neuron_recorder.get_neuron_sampling_interval(variable)

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return self.__neuron_recorder.get_neuron_sampling_interval("spikes")

    @overrides(AbstractPopulationInitializable.initialize)
    def initialize(self, variable, value, selector=None):
        if variable not in self._state_variables:
            raise KeyError(
                "Vertex does not support initialisation of"
                " parameter {}".format(variable))
        if self.__has_run:
            self._state_variables[variable].set_value_by_selector(
                selector, value)
            logger.warning(
                "initializing {} after run and before reset only changes the "
                "current state and will be lost after reset".format(variable))
        else:
            # set the inital values
            self.__initial_state_variables[variable].set_value_by_selector(
                selector, value)
            # Update the sate variables in case asked for
            self._state_variables.copy_into(self.__initial_state_variables)
        for vertex in self.machine_vertices:
            if isinstance(vertex, AbstractRewritesDataSpecification):
                vertex.set_reload_required(True)

    @property
    def initialize_parameters(self):
        """ The names of parameters that have default initial values.

        :rtype: iterable(str)
        """
        return self.__pynn_model.default_initial_values.keys()

    def _get_parameter(self, variable):
        if variable.endswith("_init"):
            # method called with "V_init"
            key = variable[:-5]
            if variable in self._state_variables:
                # variable is v and parameter is v_init
                return variable
            elif key in self._state_variables:
                # Oops neuron defines v and not v_init
                return key
        else:
            # method called with "v"
            if variable + "_init" in self._state_variables:
                # variable is v and parameter is v_init
                return variable + "_init"
            if variable in self._state_variables:
                # Oops neuron defines v and not v_init
                return variable

        # parameter not found for this variable
        raise KeyError("No variable {} found in {}".format(
            variable, self.__neuron_impl.model_name))

    @overrides(AbstractPopulationInitializable.get_initial_value)
    def get_initial_value(self, variable, selector=None):
        parameter = self._get_parameter(variable)

        ranged_list = self._state_variables[parameter]
        if selector is None:
            return ranged_list
        return ranged_list.get_values(selector)

    @property
    def conductance_based(self):
        """
        :rtype: bool
        """
        return self.__neuron_impl.is_conductance_based

    @overrides(AbstractPopulationSettable.get_value)
    def get_value(self, key):
        """ Get a property of the overall model.
        """
        if key not in self._parameters:
            raise InvalidParameterType(
                "Population {} does not have parameter {}".format(
                    self.__neuron_impl.model_name, key))
        return self._parameters[key]

    @overrides(AbstractPopulationSettable.set_value)
    def set_value(self, key, value):
        """ Set a property of the overall model.
        """
        if key not in self._parameters:
            raise InvalidParameterType(
                "Population {} does not have parameter {}".format(
                    self.__neuron_impl.model_name, key))
        self._parameters.set_value(key, value)
        for vertex in self.machine_vertices:
            if isinstance(vertex, AbstractRewritesDataSpecification):
                vertex.set_reload_required(True)

    @property
    def weight_scale(self):
        """
        :rtype: float
        """
        return self.__neuron_impl.get_global_weight_scale()

    @property
    def ring_buffer_sigma(self):
        return self.__synapse_manager.ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self.__synapse_manager.ring_buffer_sigma = ring_buffer_sigma

    def reset_ring_buffer_shifts(self):
        self.__synapse_manager.reset_ring_buffer_shifts()

    @property
    def spikes_per_second(self):
        return self.__synapse_manager.spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self.__synapse_manager.spikes_per_second = spikes_per_second

    @property
    def synapse_dynamics(self):
        """
        :rtype: AbstractSynapseDynamics
        """
        return self.__synapse_manager.synapse_dynamics

    def set_synapse_dynamics(self, synapse_dynamics):
        """
        :param AbstractSynapseDynamics synapse_dynamics:
        """
        self.__synapse_manager.synapse_dynamics = synapse_dynamics
        # If we are setting a synapse dynamics, we must remap even if the
        # change above means we don't have to
        self.__change_requires_mapping = True

    @overrides(AbstractAcceptsIncomingSynapses.get_connections_from_machine)
    def get_connections_from_machine(
            self, transceiver, placements, app_edge, synapse_info):
        # pylint: disable=too-many-arguments
        return self.__synapse_manager.get_connections_from_machine(
            transceiver, placements, app_edge, synapse_info)

    def clear_connection_cache(self):
        self.__synapse_manager.clear_connection_cache()

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        """ Gets the constraints for partitions going out of this vertex.

        :param partition: the partition that leaves this vertex
        :return: list of constraints
        """
        return [ContiguousKeyRangeContraint()]

    @overrides(AbstractNeuronRecordable.clear_recording)
    def clear_recording(self, variable, buffer_manager, placements):
        if variable == NeuronRecorder.SPIKES:
            index = len(self.__neuron_impl.get_recordable_variables())
        else:
            index = (
                self.__neuron_impl.get_recordable_variable_index(variable))
        self._clear_recording_region(buffer_manager, placements, index)

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements):
        self._clear_recording_region(
            buffer_manager, placements,
            len(self.__neuron_impl.get_recordable_variables()))

    def _clear_recording_region(
            self, buffer_manager, placements, recording_region_id):
        """ Clear a recorded data region from the buffer manager.

        :param buffer_manager: the buffer manager object
        :param placements: the placements object
        :param recording_region_id: the recorded region ID for clearing
        :rtype: None
        """
        for machine_vertex in self.machine_vertices:
            placement = placements.get_placement_of_vertex(machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p, recording_region_id)

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        if variable == NeuronRecorder.SPIKES:
            return NeuronRecorder.SPIKES
        if variable == NeuronRecorder.PACKETS:
            return "count"
        if self.__neuron_impl.is_recordable(variable):
            return self.__neuron_impl.get_recordable_units(variable)
        if variable not in self._parameters:
            raise Exception("Population {} does not have parameter {}".format(
                self.__neuron_impl.model_name, variable))
        return self.__neuron_impl.get_units(variable)

    def describe(self):
        """ Get a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see :py:mod:`pyNN.descriptions`).

        If template is None, then a dictionary containing the template context
        will be returned.

        :rtype: dict(str, ...)
        """
        parameters = dict()
        for parameter_name in self.__pynn_model.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self.__neuron_impl.model_name,
            "default_parameters": self.__pynn_model.default_parameters,
            "default_initial_values": self.__pynn_model.default_parameters,
            "parameters": parameters,
        }
        return context

    def get_synapse_id_by_target(self, target):
        return self.__neuron_impl.get_synapse_id_by_target(target)

    def __str__(self):
        return "{} with {} atoms".format(self.label, self.n_atoms)

    def __repr__(self):
        return self.__str__()

    @overrides(AbstractCanReset.reset_to_first_timestep)
    def reset_to_first_timestep(self):
        # Mark that reset has been done, and reload state variables
        self.__has_run = False
        self._state_variables.copy_into(self.__initial_state_variables)
        for vertex in self.machine_vertices:
            if isinstance(vertex, AbstractRewritesDataSpecification):
                vertex.set_reload_required(True)

        # If synapses change during the run,
        if self.__synapse_manager.changes_during_run:
            self.__change_requires_data_generation = True
            for vertex in self.machine_vertices:
                if isinstance(vertex, AbstractRewritesDataSpecification):
                    vertex.set_reload_required(True)
