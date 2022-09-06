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
import math
import numpy
from scipy import special  # @UnresolvedImport
import operator
from functools import reduce
from collections import defaultdict

from pyNN.space import Grid2D, Grid3D

from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_utilities.progress_bar import ProgressBar
from data_specification.enums.data_type import DataType
from spinn_utilities.config_holder import (
    get_config_int, get_config_float, get_config_bool)
from pacman.model.resources import MultiRegionSDRAM
from spinn_front_end_common.abstract_models import (
    AbstractChangableAfterRun, AbstractCanReset,
    AbstractRewritesDataSpecification)
from spinn_front_end_common.abstract_models.impl import (
    TDMAAwareApplicationVertex)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, SYSTEM_BYTES_REQUIREMENT)
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.interface.profiling.profile_utils import (
    get_profile_region_size)
from spinn_front_end_common.interface.buffer_management\
    .recording_utilities import (
       get_recording_header_size, get_recording_data_constant_size)
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, AbstractNeuronRecordable, AbstractEventRecordable,
    NeuronRecorder)
from spynnaker.pyNN.models.abstract_models import (
    AbstractPopulationInitializable, AbstractAcceptsIncomingSynapses,
    AbstractPopulationSettable, AbstractContainsUnits, AbstractMaxSpikes,
    HasSynapses, SupportsStructure)
from spynnaker.pyNN.exceptions import InvalidParameterType, SpynnakerException
from spynnaker.pyNN.utilities.ranged import (
    SpynnakerRangeDictionary)
from spynnaker.pyNN.utilities.constants import (
    POSSION_SIGMA_SUMMATION_LIMIT)
from spynnaker.pyNN.utilities.running_stats import RunningStats
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSDRAMSynapseDynamics, AbstractSynapseDynamicsStructural,
    AbstractSupportsSignedWeights)
from spynnaker.pyNN.models.neuron.local_only import AbstractLocalOnly
from .synapse_io import get_max_row_info
from .master_pop_table import MasterPopTableAsBinarySearch
from .generator_data import GeneratorData
from .synaptic_matrices import SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES

logger = FormatAdapter(logging.getLogger(__name__))

# TODO: Make sure these values are correct (particularly CPU cycles)
_NEURON_BASE_DTCM_USAGE_IN_BYTES = 9 * BYTES_PER_WORD
_NEURON_BASE_N_CPU_CYCLES_PER_NEURON = 22
_NEURON_BASE_N_CPU_CYCLES = 10

# 1 for number of neurons
# 1 for number of synapse types
# 1 for number of neuron bits
# 1 for number of synapse type bits
# 1 for number of delay bits
# 1 for drop late packets,
# 1 for incoming spike buffer size
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 7 * BYTES_PER_WORD


def _prod(iterable):
    """ Finds the product of the iterable

    :param iterable iterable: Things to multiply together
    """
    return reduce(operator.mul, iterable, 1)


class AbstractPopulationVertex(
        TDMAAwareApplicationVertex, AbstractContainsUnits,
        AbstractSpikeRecordable, AbstractNeuronRecordable,
        AbstractEventRecordable,
        AbstractPopulationInitializable, AbstractPopulationSettable,
        AbstractChangableAfterRun, AbstractAcceptsIncomingSynapses,
        AbstractCanReset, SupportsStructure):
    """ Underlying vertex model for Neural Populations.\
        Not actually abstract.
    """

    __slots__ = [
        "__all_single_syn_sz",
        "__change_requires_mapping",
        "__change_requires_data_generation",
        "__incoming_spike_buffer_size",
        "__n_atoms",
        "__n_profile_samples",
        "__neuron_impl",
        "__neuron_recorder",
        "__synapse_recorder",
        "_parameters",  # See AbstractPyNNModel
        "__pynn_model",
        "_state_variables",  # See AbstractPyNNModel
        "__initial_state_variables",
        "__has_run",
        "__updated_state_variables",
        "__ring_buffer_sigma",
        "__spikes_per_second",
        "__drop_late_spikes",
        "__incoming_projections",
        "__synapse_dynamics",
        "__max_row_info",
        "__self_projection",
        "__current_sources",
        "__current_source_id_list",
        "__structure"]

    #: recording region IDs
    _SPIKE_RECORDING_REGION = 0

    #: the size of the runtime SDP port data region
    _RUNTIME_SDP_PORT_SIZE = BYTES_PER_WORD

    #: The Buffer traffic type
    _TRAFFIC_IDENTIFIER = "BufferTraffic"

    _C_MAIN_BASE_N_CPU_CYCLES = 0
    _NEURON_BASE_N_CPU_CYCLES_PER_NEURON = 22
    _NEURON_BASE_N_CPU_CYCLES = 10
    _SYNAPSE_BASE_N_CPU_CYCLES_PER_NEURON = 22
    _SYNAPSE_BASE_N_CPU_CYCLES = 10

    # 5 elements before the start of global parameters
    # 1. has key, 2. n atoms, 3. n_atoms_peak 4. n_synapse_types
    BYTES_TILL_START_OF_GLOBAL_PARAMETERS = 4 * BYTES_PER_WORD

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

        # pylint: disable=too-many-arguments
        super().__init__(label, constraints, max_atoms_per_core, splitter)

        self.__n_atoms = self.round_n_atoms(n_neurons, "n_neurons")

        # buffer data
        self.__incoming_spike_buffer_size = incoming_spike_buffer_size

        if incoming_spike_buffer_size is None:
            self.__incoming_spike_buffer_size = get_config_int(
                "Simulation", "incoming_spike_buffer_size")

        # Limit the DTCM used by one-to-one connections
        self.__all_single_syn_sz = get_config_int(
            "Simulation", "one_to_one_connection_dtcm_max_bytes")

        self.__ring_buffer_sigma = ring_buffer_sigma
        if self.__ring_buffer_sigma is None:
            self.__ring_buffer_sigma = get_config_float(
                "Simulation", "ring_buffer_sigma")

        self.__spikes_per_second = spikes_per_second
        if self.__spikes_per_second is None:
            self.__spikes_per_second = get_config_float(
                "Simulation", "spikes_per_second")

        self.__drop_late_spikes = drop_late_spikes
        if self.__drop_late_spikes is None:
            self.__drop_late_spikes = get_config_bool(
                "Simulation", "drop_late_spikes")

        self.__neuron_impl = neuron_impl
        self.__pynn_model = pynn_model
        self._parameters = SpynnakerRangeDictionary(n_neurons)
        self.__neuron_impl.add_parameters(self._parameters)
        self.__initial_state_variables = SpynnakerRangeDictionary(n_neurons)
        self.__neuron_impl.add_state_variables(self.__initial_state_variables)
        self._state_variables = self.__initial_state_variables.copy()

        # Set up for recording
        neuron_recordable_variables = list(
            self.__neuron_impl.get_recordable_variables())
        record_data_types = dict(
            self.__neuron_impl.get_recordable_data_types())
        self.__neuron_recorder = NeuronRecorder(
            neuron_recordable_variables, record_data_types,
            [NeuronRecorder.SPIKES], n_neurons, [], {}, [], {})
        self.__synapse_recorder = NeuronRecorder(
            [], {}, [],
            n_neurons, [NeuronRecorder.PACKETS],
            {NeuronRecorder.PACKETS: NeuronRecorder.PACKETS_TYPE},
            [NeuronRecorder.REWIRING],
            {NeuronRecorder.REWIRING: NeuronRecorder.REWIRING_TYPE})

        # bool for if state has changed.
        self.__change_requires_mapping = True
        self.__change_requires_data_generation = False
        self.__has_run = False

        # Current sources for this vertex
        self.__current_sources = []
        self.__current_source_id_list = dict()

        # Set up for profiling
        self.__n_profile_samples = get_config_int(
            "Reports", "n_profile_samples")

        # Set up for incoming
        self.__incoming_projections = defaultdict(list)
        self.__max_row_info = dict()
        self.__self_projection = None

        # Prepare for dealing with STDP - there can only be one (non-static)
        # synapse dynamics per vertex at present
        self.__synapse_dynamics = None

        self.__structure = None

    @overrides(TDMAAwareApplicationVertex.get_max_atoms_per_core)
    def get_max_atoms_per_core(self):
        max_atoms = super().get_max_atoms_per_core()

        if self.__synapse_dynamics is None:
            return max_atoms

        # Dynamically adjust depending on the needs of the synapse dynamics
        return min(
            max_atoms, self.__synapse_dynamics.absolute_max_atoms_per_core)

    @overrides(TDMAAwareApplicationVertex.get_max_atoms_per_dimension_per_core)
    def get_max_atoms_per_dimension_per_core(self):
        max_atoms = self.get_max_atoms_per_core()

        # If single dimensional, we can use the max atoms calculation
        if len(self.atoms_shape) == 1:
            return (max_atoms, )

        # If not, the user has to be more specific if the total number of
        # atoms is not small enough to fit on one core
        max_per_dim = super().get_max_atoms_per_dimension_per_core()
        if numpy.prod(max_per_dim) > max_atoms:
            raise SpynnakerException(
                "When using a multi-dimensional vertex, a maximum number of"
                " neurons for each dimension must be provided such that the"
                " total number of neurons per core is less than or equal to"
                f" {max_atoms}")
        return max_per_dim

    @overrides(TDMAAwareApplicationVertex.set_max_atoms_per_dimension_per_core)
    def set_max_atoms_per_dimension_per_core(self, new_value):
        if self.__synapse_dynamics is not None:
            max_atoms = self.__synapse_dynamics.absolute_max_atoms_per_core
            if numpy.prod(new_value) > max_atoms:
                raise SpynnakerException(
                    "In the current configuration, the maximum number of"
                    " neurons for each dimension must be such that the total"
                    " number of neurons per core is less than or equal to"
                    f" {max_atoms}")
        super().set_max_atoms_per_dimension_per_core(new_value)

    @overrides(SupportsStructure.set_structure)
    def set_structure(self, structure):
        self.__structure = structure

    @property
    def synapse_dynamics(self):
        """ The synapse dynamics used by the synapses e.g. plastic or static.
            Settable.

        :rtype: AbstractSynapseDynamics or None
        """
        return self.__synapse_dynamics

    @synapse_dynamics.setter
    def synapse_dynamics(self, synapse_dynamics):
        """ Set the synapse dynamics.  Note that after setting, the dynamics
            might not be the type set as it can be combined with the existing
            dynamics in exciting ways.

        :param AbstractSynapseDynamics synapse_dynamics:
            The synapse dynamics to set
        """
        if self.__synapse_dynamics is None:
            self.__synapse_dynamics = synapse_dynamics
        else:
            self.__synapse_dynamics = self.__synapse_dynamics.merge(
                synapse_dynamics)

    def add_incoming_projection(self, projection):
        """ Add a projection incoming to this vertex

        :param PyNNProjectionCommon projection:
            The new projection to add
        """
        # Reset the ring buffer shifts as a projection has been added
        self.__change_requires_mapping = True
        self.__max_row_info.clear()
        # pylint: disable=protected-access
        pre_vertex = projection._projection_edge.pre_vertex
        self.__incoming_projections[pre_vertex].append(projection)
        if pre_vertex == self:
            self.__self_projection = projection

    @property
    def self_projection(self):
        """ Get any projection from this vertex to itself

        :rtype: PyNNProjectionCommon or None
        """
        return self.__self_projection

    @property
    @overrides(TDMAAwareApplicationVertex.n_atoms)
    def n_atoms(self):
        return self.__n_atoms

    @property
    @overrides(TDMAAwareApplicationVertex.atoms_shape)
    def atoms_shape(self):
        if isinstance(self.__structure, (Grid2D, Grid3D)):
            return self.__structure.calculate_size(self.__n_atoms)
        return super(AbstractPopulationVertex, self).atoms_shape

    @overrides(TDMAAwareApplicationVertex.get_n_cores)
    def get_n_cores(self):
        return len(self._splitter.get_out_going_slices())

    @property
    def size(self):
        """ The number of neurons in the vertex

        :rtype: int
        """
        return self.__n_atoms

    @property
    def all_single_syn_size(self):
        """ The maximum amount of DTCM to use for single synapses

        :rtype: int
        """
        return self.__all_single_syn_sz

    @property
    def direct_matrix_size(self):
        """ The size of the direct matrix region in bytes

        :rtype: int
        """
        # An additional word is used for the size of the region
        return self.__all_single_syn_sz + BYTES_PER_WORD

    @property
    def incoming_spike_buffer_size(self):
        """ The size of the incoming spike buffer to be used on the cores

        :rtype: int
        """
        return self.__incoming_spike_buffer_size

    @property
    def parameters(self):
        """ The parameters of the neurons in the population

        :rtype: SpyNNakerRangeDictionary
        """
        return self._parameters

    @property
    def state_variables(self):
        """ The state variables of the neuron in the population

        :rtype: SpyNNakerRangeDicationary
        """
        return self._state_variables

    @property
    def neuron_impl(self):
        """ The neuron implementation

        :rtype: AbstractNeuronImpl
        """
        return self.__neuron_impl

    @property
    def n_profile_samples(self):
        """ The maximum number of profile samples to report

        :rtype: int
        """
        return self.__n_profile_samples

    @property
    def neuron_recorder(self):
        """ The recorder for neurons

        :rtype: NeuronRecorder
        """
        return self.__neuron_recorder

    @property
    def synapse_recorder(self):
        """ The recorder for synapses

        :rtype: SynapseRecorder
        """
        return self.__synapse_recorder

    @property
    def drop_late_spikes(self):
        """ Whether spikes should be dropped if not processed in a timestep

        :rtype: bool
        """
        return self.__drop_late_spikes

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
        self.__change_requires_mapping = False
        self.__change_requires_data_generation = False

    def get_neuron_params_position(self, n_atoms):
        """ Get the position of the neuron parameters themselves within the
            neuron parameters region

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the slice of atoms.
        :rtype: int
        """
        return (
            # Parameters global for the neurons
            self.BYTES_TILL_START_OF_GLOBAL_PARAMETERS +
            # The ring buffer shifts
            (self.__neuron_impl.get_n_synapse_types() * BYTES_PER_WORD) +
            # TDMA parameters
            self.tdma_sdram_size_in_bytes +
            # The keys per neuron
            n_atoms * BYTES_PER_WORD)

    def get_sdram_usage_for_neuron_params(self, n_atoms):
        """ Calculate the SDRAM usage for just the neuron parameters region.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            the slice of atoms.
        :return: The SDRAM required for the neuron region
        """
        return (
            self.get_neuron_params_position(n_atoms) +
            self.__neuron_impl.get_sdram_usage_in_bytes(n_atoms))

    def get_sdram_usage_for_current_source_params(self, n_atoms):
        """ Calculate the SDRAM usage for the current source parameters region.

        :param int n_atoms: The number of atoms to account for
        :return: The SDRAM required for the current source region
        """
        # If non at all, just output size of 0 declaration
        if not self.__current_sources:
            return BYTES_PER_WORD

        # This is a worst-case count, assuming all sources apply to all atoms
        # Start with the count of sources + count of sources per neuron
        sdram_usage = BYTES_PER_WORD + (n_atoms * BYTES_PER_WORD)

        # There is a number of each different type of current source
        sdram_usage += 4 * BYTES_PER_WORD

        # Add on size of neuron id list per source (remember assume all atoms)
        sdram_usage += (
            len(self.__current_sources) * 2 * n_atoms * BYTES_PER_WORD)

        # Add on the size of the current source data + neuron id list per
        # source (remember, assume all neurons for worst case)
        for current_source in self.__current_sources:
            sdram_usage += current_source.get_sdram_usage_in_bytes()

        return sdram_usage

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__neuron_recorder.is_recording(NeuronRecorder.SPIKES)

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        self.set_recording(
            NeuronRecorder.SPIKES, new_state, sampling_interval, indexes)

    @overrides(AbstractEventRecordable.is_recording_events)
    def is_recording_events(self, variable):
        return self.__synapse_recorder.is_recording(variable)

    @overrides(AbstractEventRecordable.set_recording_events)
    def set_recording_events(
            self, variable, new_state=True, sampling_interval=None,
            indexes=None):
        self.set_recording(
            variable, new_state, sampling_interval, indexes)

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(self):
        return self.__neuron_recorder.get_spikes(
            self.label, self, NeuronRecorder.SPIKES)

    @overrides(AbstractEventRecordable.get_events)
    def get_events(self, variable):
        return self.__synapse_recorder.get_events(
            self.label, self, variable)

    @overrides(AbstractNeuronRecordable.get_recordable_variables)
    def get_recordable_variables(self):
        variables = list()
        variables.extend(self.__neuron_recorder.get_recordable_variables())
        variables.extend(self.__synapse_recorder.get_recordable_variables())
        return variables

    def __raise_var_not_supported(self, variable):
        """ Helper to indicate that recording a variable is not supported

        :param str variable: The variable to report as unsupported
        """
        msg = ("Variable {} is not supported. Supported variables are"
               "{}".format(variable, self.get_recordable_variables()))
        raise ConfigurationException(msg)

    @overrides(AbstractNeuronRecordable.is_recording)
    def is_recording(self, variable):
        if self.__neuron_recorder.is_recordable(variable):
            return self.__neuron_recorder.is_recording(variable)
        if self.__synapse_recorder.is_recordable(variable):
            return self.__synapse_recorder.is_recording(variable)
        self.__raise_var_not_supported(variable)

    @overrides(AbstractNeuronRecordable.set_recording)
    def set_recording(self, variable, new_state=True, sampling_interval=None,
                      indexes=None):
        if self.__neuron_recorder.is_recordable(variable):
            self.__neuron_recorder.set_recording(
                variable, new_state, sampling_interval, indexes)
        elif self.__synapse_recorder.is_recordable(variable):
            self.__synapse_recorder.set_recording(
                variable, new_state, sampling_interval, indexes)
        else:
            self.__raise_var_not_supported(variable)
        self.__change_requires_mapping = not self.is_recording(variable)

    def get_data(self, variable):
        # pylint: disable=too-many-arguments
        if self.__neuron_recorder.is_recordable(variable):
            return self.__neuron_recorder.get_matrix_data(
                self.label, self, variable)
        elif self.__synapse_recorder.is_recordable(variable):
            return self.__synapse_recorder.get_matrix_data(
                self.label, self, variable)
        self.__raise_var_not_supported(variable)

    @overrides(AbstractNeuronRecordable.get_neuron_sampling_interval)
    def get_neuron_sampling_interval(self, variable):
        if self.__neuron_recorder.is_recordable(variable):
            return self.__neuron_recorder.get_neuron_sampling_interval(
                variable)
        elif self.__synapse_recorder.is_recordable(variable):
            return self.__synapse_recorder.get_neuron_sampling_interval(
                variable)
        self.__raise_var_not_supported(variable)

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return self.__neuron_recorder.get_neuron_sampling_interval("spikes")

    @overrides(AbstractEventRecordable.get_events_sampling_interval)
    def get_events_sampling_interval(self, variable):
        return self.__neuron_recorder.get_neuron_sampling_interval(variable)

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
        """ Get a neuron parameter value

        :param str variable: The variable to get the value of
        """
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
        return self.__ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self.__ring_buffer_sigma = ring_buffer_sigma

    @property
    def spikes_per_second(self):
        return self.__spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self.__spikes_per_second = spikes_per_second

    def set_synapse_dynamics(self, synapse_dynamics):
        """ Set the synapse dynamics of this population

        :param AbstractSynapseDynamics synapse_dynamics:
            The synapse dynamics to set
        """
        self.synapse_dynamics = synapse_dynamics

    def clear_connection_cache(self):
        """ Flush the cache of connection information; needed for a second run
        """
        for post_vertex in self.machine_vertices:
            if isinstance(post_vertex, HasSynapses):
                post_vertex.clear_connection_cache()

    @overrides(AbstractNeuronRecordable.clear_recording)
    def clear_recording(self, variable):
        if variable == NeuronRecorder.SPIKES:
            index = len(self.__neuron_impl.get_recordable_variables())
        elif variable == NeuronRecorder.REWIRING:
            index = len(self.__neuron_impl.get_recordable_variables()) + 1
        else:
            index = (
                self.__neuron_impl.get_recordable_variable_index(variable))
        self._clear_recording_region(index)

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self):
        self._clear_recording_region(
            len(self.__neuron_impl.get_recordable_variables()))

    @overrides(AbstractEventRecordable.clear_event_recording)
    def clear_event_recording(self):
        self._clear_recording_region(
            len(self.__neuron_impl.get_recordable_variables()) + 1)

    def _clear_recording_region(self, recording_region_id):
        """ Clear a recorded data region from the buffer manager.

        :param recording_region_id: the recorded region ID for clearing
        :rtype: None
        """
        buffer_manager = SpynnakerDataView.get_buffer_manager()
        for machine_vertex in self.machine_vertices:
            placement = SpynnakerDataView.get_placement_of_vertex(
                machine_vertex)
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
        """ Get the id of synapse using its target name

        :param str target: The synapse to get the id of
        """
        return self.__neuron_impl.get_synapse_id_by_target(target)

    def inject(self, current_source, neuron_list):
        """ Inject method from population to set up current source

        """
        self.__current_sources.append(current_source)
        self.__current_source_id_list[current_source] = neuron_list
        # set the associated vertex (for multi-run case)
        current_source.set_app_vertex(self)
        # set to reload for multi-run case
        for m_vertex in self.machine_vertices:
            m_vertex.set_reload_required(True)

    @property
    def current_sources(self):
        """ Current sources need to be available to machine vertex

        """
        return self.__current_sources

    @property
    def current_source_id_list(self):
        """ Current source ID list needs to be available to machine vertex

        """
        return self.__current_source_id_list

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
        if (self.__synapse_dynamics is not None and
                self.__synapse_dynamics.changes_during_run):
            self.__change_requires_data_generation = True
            for vertex in self.machine_vertices:
                if isinstance(vertex, AbstractRewritesDataSpecification):
                    vertex.set_reload_required(True)

    @staticmethod
    def _ring_buffer_expected_upper_bound(
            weight_mean, weight_std_dev, spikes_per_second,
            n_synapses_in, sigma):
        """ Provides expected upper bound on accumulated values in a ring\
            buffer element.

        Requires an assessment of maximum Poisson input rate.

        Assumes knowledge of mean and SD of weight distribution, fan-in\
        and timestep.

        All arguments should be assumed real values except n_synapses_in\
        which will be an integer.

        :param float weight_mean: Mean of weight distribution (in either nA or\
            microSiemens as required)
        :param float weight_std_dev: SD of weight distribution
        :param float spikes_per_second: Maximum expected Poisson rate in Hz
        :param int machine_timestep: in us
        :param int n_synapses_in: No of connected synapses
        :param float sigma: How many SD above the mean to go for upper bound;\
            a good starting choice is 5.0. Given length of simulation we can\
            set this for approximate number of saturation events.
        :rtype: float
        """
        # E[ number of spikes ] in a timestep
        average_spikes_per_timestep = (
            float(n_synapses_in * spikes_per_second) /
            SpynnakerDataView.get_simulation_time_step_per_s())

        # Exact variance contribution from inherent Poisson variation
        poisson_variance = average_spikes_per_timestep * (weight_mean ** 2)

        # Upper end of range for Poisson summation required below
        # upper_bound needs to be an integer
        upper_bound = int(round(average_spikes_per_timestep +
                                POSSION_SIGMA_SUMMATION_LIMIT *
                                math.sqrt(average_spikes_per_timestep)))

        # Closed-form exact solution for summation that gives the variance
        # contributed by weight distribution variation when modulated by
        # Poisson PDF.  Requires scipy.special for gamma and incomplete gamma
        # functions. Beware: incomplete gamma doesn't work the same as
        # Mathematica because (1) it's regularised and needs a further
        # multiplication and (2) it's actually the complement that is needed
        # i.e. 'gammaincc']

        weight_variance = 0.0

        if weight_std_dev > 0:
            # pylint: disable=no-member
            lngamma = special.gammaln(1 + upper_bound)
            gammai = special.gammaincc(
                1 + upper_bound, average_spikes_per_timestep)

            big_ratio = (math.log(average_spikes_per_timestep) * upper_bound -
                         lngamma)

            if -701.0 < big_ratio < 701.0 and big_ratio != 0.0:
                log_weight_variance = (
                    -average_spikes_per_timestep +
                    math.log(average_spikes_per_timestep) +
                    2.0 * math.log(weight_std_dev) +
                    math.log(math.exp(average_spikes_per_timestep) * gammai -
                             math.exp(big_ratio)))
                weight_variance = math.exp(log_weight_variance)

        # upper bound calculation -> mean + n * SD
        return ((average_spikes_per_timestep * weight_mean) +
                (sigma * math.sqrt(poisson_variance + weight_variance)))

    def get_ring_buffer_shifts(self):
        """ Get the shift of the ring buffers for transfer of values into the
            input buffers for this model.

        :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
            The projections to consider in the calculations
        :rtype: list(int)
        """
        stats = _Stats(self.__neuron_impl, self.__spikes_per_second,
                       self.__ring_buffer_sigma)

        for proj in self.incoming_projections:
            # pylint: disable=protected-access
            synapse_info = proj._synapse_information
            # Skip if this is a synapse dynamics synapse type
            if synapse_info.synapse_type_from_dynamics:
                continue
            stats.add_projection(proj)

        n_synapse_types = self.__neuron_impl.get_n_synapse_types()
        max_weights = numpy.zeros(n_synapse_types)
        for synapse_type in range(n_synapse_types):
            max_weights[synapse_type] = stats.get_max_weight(synapse_type)

        # Convert these to powers; we could use int.bit_length() for this if
        # they were integers, but they aren't...
        max_weight_powers = (
            0 if w <= 0 else int(math.ceil(max(0, math.log2(w))))
            for w in max_weights)

        # If 2^max_weight_power equals the max weight, we have to add another
        # power, as range is 0 - (just under 2^max_weight_power)!
        max_weight_powers = (
            w + 1 if (2 ** w) <= a else w
            for w, a in zip(max_weight_powers, max_weights))

        return list(max_weight_powers)

    @staticmethod
    def __get_weight_scale(ring_buffer_to_input_left_shift):
        """ Return the amount to scale the weights by to convert them from \
            floating point values to 16-bit fixed point numbers which can be \
            shifted left by ring_buffer_to_input_left_shift to produce an\
            s1615 fixed point number

        :param int ring_buffer_to_input_left_shift:
        :rtype: float
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))

    def get_weight_scales(self, ring_buffer_shifts):
        """ Get the weight scaling to apply to weights in synapses

        :param list(int) ring_buffer_shifts:
            The shifts to convert to weight scales
        :rtype: list(int)
        """
        weight_scale = self.__neuron_impl.get_global_weight_scale()
        return numpy.array([
            self.__get_weight_scale(r) * weight_scale
            for r in ring_buffer_shifts])

    @overrides(AbstractAcceptsIncomingSynapses.get_connections_from_machine)
    def get_connections_from_machine(
            self, app_edge, synapse_info):
        # Start with something in the list so that concatenate works
        connections = [numpy.zeros(
                0, dtype=AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE)]
        progress = ProgressBar(
            len(self.machine_vertices),
            "Getting synaptic data between {} and {}".format(
                app_edge.pre_vertex.label, app_edge.post_vertex.label))
        for post_vertex in progress.over(self.machine_vertices):
            if isinstance(post_vertex, HasSynapses):
                placement = SpynnakerDataView.get_placement_of_vertex(
                    post_vertex)
                connections.extend(post_vertex.get_connections_from_machine(
                    placement, app_edge, synapse_info))
        return numpy.concatenate(connections)

    def get_synapse_params_size(self):
        """ Get the size of the synapse parameters in bytes

        :rtype: int
        """
        # This will only hold ring buffer scaling for the neuron synapse
        # types
        return (_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES +
                (BYTES_PER_WORD * self.__neuron_impl.get_n_synapse_types()))

    def get_synapse_dynamics_size(self, n_atoms):
        """ Get the size of the synapse dynamics region

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the vertex to get the usage of
        :rtype: int
        """
        if self.__synapse_dynamics is None:
            return 0

        if isinstance(self.__synapse_dynamics, AbstractLocalOnly):
            return self.__synapse_dynamics.get_parameters_usage_in_bytes(
                self.incoming_projections)

        return self.__synapse_dynamics.get_parameters_sdram_usage_in_bytes(
            n_atoms, self.__neuron_impl.get_n_synapse_types())

    def get_structural_dynamics_size(self, n_atoms):
        """ Get the size of the structural dynamics region

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the vertex to get the usage of
        :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
            The projections to consider in the calculations
        """
        if self.__synapse_dynamics is None:
            return 0

        if not isinstance(
                self.__synapse_dynamics, AbstractSynapseDynamicsStructural):
            return 0

        return self.__synapse_dynamics\
            .get_structural_parameters_sdram_usage_in_bytes(
                self.incoming_projections, n_atoms)

    def get_synapses_size(self, n_post_atoms):
        """ Get the maximum SDRAM usage for the synapses on a vertex slice

        :param int n_post_atoms: The number of atoms projected to
        :param list(~spynnaker.pyNN.models.Projection) incoming_projections:
            The projections to consider in the calculations
        """
        addr = 2 * BYTES_PER_WORD
        for proj in self.incoming_projections:
            addr = self.__add_matrix_size(addr, proj, n_post_atoms)
        return addr

    def __add_matrix_size(self, addr, projection, n_post_atoms):
        """ Add to the address the size of the matrices for the projection to
            the vertex slice

        :param int addr: The address to start from
        :param ~spynnaker.pyNN.models.Projection: The projection to add
        :param int n_post_atoms: The number of atoms projected to
        :rtype: int
        """
        # pylint: disable=protected-access
        synapse_info = projection._synapse_information
        app_edge = projection._projection_edge

        max_row_info = self.get_max_row_info(
            synapse_info, n_post_atoms, app_edge)

        vertex = app_edge.pre_vertex
        max_atoms = vertex.get_max_atoms_per_core()
        n_sub_atoms = int(min(max_atoms, vertex.n_atoms))
        n_sub_edges = int(math.ceil(vertex.n_atoms / n_sub_atoms))

        if max_row_info.undelayed_max_n_synapses > 0:
            size = n_sub_atoms * max_row_info.undelayed_max_bytes
            for _ in range(n_sub_edges):
                addr = MasterPopTableAsBinarySearch.get_next_allowed_address(
                    addr)
                addr += size
        if max_row_info.delayed_max_n_synapses > 0:
            size = (n_sub_atoms * max_row_info.delayed_max_bytes *
                    app_edge.n_delay_stages)
            for _ in range(n_sub_edges):
                addr = MasterPopTableAsBinarySearch.get_next_allowed_address(
                    addr)
                addr += size
        return addr

    def get_max_row_info(self, synapse_info, n_post_atoms, app_edge):
        """ Get maximum row length data

        :param SynapseInformation synapse_info: Information about synapses
        :param int n_post_atoms: The number of atoms projected to
        :param ProjectionApplicationEdge app_edge: The edge of the projection
        """
        key = (app_edge, synapse_info, n_post_atoms)
        if key in self.__max_row_info:
            return self.__max_row_info[key]
        max_row_info = get_max_row_info(
            synapse_info, n_post_atoms, app_edge.n_delay_stages, app_edge)
        self.__max_row_info[key] = max_row_info
        return max_row_info

    def get_synapse_expander_size(self):
        """ Get the size of the synapse expander region in bytes

        :rtype: int
        """
        size = 0
        for proj in self.incoming_projections:
            # pylint: disable=protected-access
            synapse_info = proj._synapse_information
            app_edge = proj._projection_edge
            n_sub_edges = len(
                app_edge.pre_vertex.splitter.get_out_going_slices())
            if not n_sub_edges:
                vertex = app_edge.pre_vertex
                max_atoms = float(min(vertex.get_max_atoms_per_core(),
                                      vertex.n_atoms))
                n_sub_edges = int(math.ceil(vertex.n_atoms / max_atoms))
            size += self.__generator_info_size(synapse_info) * n_sub_edges

        # If anything generates data, also add some base information
        if size:
            size += SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES
            size += (self.__neuron_impl.get_n_synapse_types() *
                     DataType.U3232.size)
        return size

    @staticmethod
    def __generator_info_size(synapse_info):
        """ The number of bytes required by the generator information

        :param SynapseInformation synapse_info: The synapse information to use

        :rtype: int
        """
        if not synapse_info.may_generate_on_machine():
            return 0

        connector = synapse_info.connector
        dynamics = synapse_info.synapse_dynamics
        gen_size = sum((
            GeneratorData.BASE_SIZE,
            connector.gen_delay_params_size_in_bytes(synapse_info.delays),
            connector.gen_weight_params_size_in_bytes(synapse_info.weights),
            connector.gen_connector_params_size_in_bytes,
            dynamics.gen_matrix_params_size_in_bytes
        ))
        return gen_size

    @property
    def synapse_executable_suffix(self):
        """ The suffix of the executable name due to the type of synapses \
            in use.

        :rtype: str
        """
        if self.__synapse_dynamics is None:
            return ""
        return self.__synapse_dynamics.get_vertex_executable_suffix()

    @property
    def neuron_recordables(self):
        """ Get the names of variables that can be recorded by the neuron

        :rtype: list(str)
        """
        return self.__neuron_recorder.get_recordable_variables()

    @property
    def synapse_recordables(self):
        """ Get the names of variables that can be recorded by the synapses

        :rtype: list(str)
        """
        return self.__synapse_recorder.get_recordable_variables()

    def get_common_constant_sdram(
            self, n_record, n_provenance, common_regions):
        """ Get the amount of SDRAM used by common parts

        :param int n_record: The number of recording regions
        :param int n_provenance: The number of provenance items
        :param CommonRegions common_regions: Region IDs
        :rtype: int
        """
        sdram = MultiRegionSDRAM()
        sdram.add_cost(common_regions.system, SYSTEM_BYTES_REQUIREMENT)
        sdram.add_cost(
            common_regions.recording,
            get_recording_header_size(n_record) +
            get_recording_data_constant_size(n_record))
        sdram.add_cost(
            common_regions.provenance,
            ProvidesProvenanceDataFromMachineImpl.get_provenance_data_size(
                n_provenance))
        sdram.add_cost(
            common_regions.profile,
            get_profile_region_size(self.__n_profile_samples))
        return sdram

    def get_neuron_variable_sdram(self, vertex_slice):
        """ Get the amount of SDRAM per timestep used by neuron parts

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of

        :rtype: int
        """
        return self.__neuron_recorder.get_variable_sdram_usage(vertex_slice)

    def get_max_neuron_variable_sdram(self, n_neurons):
        """ Get the amount of SDRAM per timestep used by neuron parts

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of

        :rtype: int
        """
        return self.__neuron_recorder.get_max_variable_sdram_usage(n_neurons)

    def get_synapse_variable_sdram(self, vertex_slice):

        """ Get the amount of SDRAM per timestep used by synapse parts

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of

        :rtype: int
        """
        if isinstance(self.__synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            self.__synapse_recorder.set_max_rewires_per_ts(
                self.__synapse_dynamics.get_max_rewires_per_ts())
        return self.__synapse_recorder.get_variable_sdram_usage(vertex_slice)

    def get_max_synapse_variable_sdram(self, n_neurons):

        """ Get the amount of SDRAM per timestep used by synapse parts

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of

        :rtype: int
        """
        if isinstance(self.__synapse_dynamics,
                      AbstractSynapseDynamicsStructural):
            self.__synapse_recorder.set_max_rewires_per_ts(
                self.__synapse_dynamics.get_max_rewires_per_ts())
        return self.__synapse_recorder.get_max_variable_sdram_usage(n_neurons)

    def get_neuron_constant_sdram(self, n_atoms, neuron_regions):

        """ Get the amount of fixed SDRAM used by neuron parts

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of
        :param NeuronRegions neuron_regions: Region IDs
        :rtype: int
        """
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            neuron_regions.neuron_params,
            self.get_sdram_usage_for_neuron_params(n_atoms))
        sdram.add_cost(
            neuron_regions.current_source_params,
            self.get_sdram_usage_for_current_source_params(n_atoms))
        sdram.add_cost(
            neuron_regions.neuron_recording,
            self.__neuron_recorder.get_metadata_sdram_usage_in_bytes(
                n_atoms))
        return sdram

    @property
    def incoming_projections(self):
        """ The projections that target this population vertex

        :rtype: iterable(~spynnaker.pyNN.models.projection.Projection)
        """
        for proj_list in self.__incoming_projections.values():
            for proj in proj_list:
                yield proj

    def get_incoming_projections_from(self, source_vertex):
        """ Get the projections that target this population vertex from
            the given source
        """
        return self.__incoming_projections[source_vertex]


class _Stats(object):
    """ Object to keep hold of and process statistics for ring buffer scaling
    """
    __slots__ = [
        "w_scale",
        "w_scale_sq",
        "n_synapse_types",
        "running_totals",
        "delay_running_totals",
        "total_weights",
        "biggest_weight",
        "rate_stats",
        "steps_per_second",
        "default_spikes_per_second",
        "ring_buffer_sigma"
    ]

    def __init__(
            self, neuron_impl, default_spikes_per_second, ring_buffer_sigma):
        self.w_scale = neuron_impl.get_global_weight_scale()
        self.w_scale_sq = self.w_scale ** 2
        n_synapse_types = neuron_impl.get_n_synapse_types()

        self.running_totals = [
            RunningStats() for _ in range(n_synapse_types)]
        self.delay_running_totals = [
            RunningStats() for _ in range(n_synapse_types)]
        self.total_weights = numpy.zeros(n_synapse_types)
        self.biggest_weight = numpy.zeros(n_synapse_types)
        self.rate_stats = [RunningStats() for _ in range(n_synapse_types)]

        self.steps_per_second = (
            SpynnakerDataView.get_simulation_time_step_per_s())
        self.default_spikes_per_second = default_spikes_per_second
        self.ring_buffer_sigma = ring_buffer_sigma

    def add_projection(self, proj):
        # pylint: disable=protected-access
        s_dynamics = proj._synapse_information.synapse_dynamics
        if isinstance(s_dynamics, AbstractSupportsSignedWeights):
            self.__add_signed_projection(proj)
        else:
            self.__add_unsigned_projection(proj)

    def __add_signed_projection(self, proj):
        # pylint: disable=protected-access
        s_info = proj._synapse_information
        connector = s_info.connector
        s_dynamics = s_info.synapse_dynamics

        n_conns = connector.get_n_connections_to_post_vertex_maximum(s_info)
        d_var = s_dynamics.get_delay_variance(connector, s_info.delays, s_info)

        s_type_pos = s_dynamics.get_positive_synapse_index(proj)
        w_mean_pos = s_dynamics.get_mean_positive_weight(proj)
        w_var_pos = s_dynamics.get_variance_positive_weight(proj)
        w_max_pos = s_dynamics.get_maximum_positive_weight(proj)
        self.__add_details(
            proj, s_type_pos, n_conns, w_mean_pos, w_var_pos, w_max_pos, d_var)

        s_type_neg = s_dynamics.get_negative_synapse_index(proj)
        w_mean_neg = -s_dynamics.get_mean_negative_weight(proj)
        w_var_neg = -s_dynamics.get_variance_negative_weight(proj)
        w_max_neg = -s_dynamics.get_minimum_negative_weight(proj)
        self.__add_details(
            proj, s_type_neg, n_conns, w_mean_neg, w_var_neg, w_max_neg, d_var)

    def __add_unsigned_projection(self, proj):
        # pylint: disable=protected-access
        s_info = proj._synapse_information
        s_type = s_info.synapse_type
        s_dynamics = s_info.synapse_dynamics
        connector = s_info.connector

        n_conns = connector.get_n_connections_to_post_vertex_maximum(s_info)
        w_mean = s_dynamics.get_weight_mean(connector, s_info)
        w_var = s_dynamics.get_weight_variance(
            connector, s_info.weights, s_info)
        w_max = s_dynamics.get_weight_maximum(connector, s_info)
        d_var = s_dynamics.get_delay_variance(connector, s_info.delays, s_info)
        self.__add_details(proj, s_type, n_conns, w_mean, w_var, w_max, d_var)

    def __add_details(
            self, proj, s_type, n_conns, w_mean, w_var, w_max, d_var):
        self.running_totals[s_type].add_items(
            w_mean * self.w_scale, w_var * self.w_scale_sq, n_conns)
        self.biggest_weight[s_type] = max(
            self.biggest_weight[s_type], w_max * self.w_scale)
        self.delay_running_totals[s_type].add_items(0.0, d_var, n_conns)

        spikes_per_tick, spikes_per_second = self.__pre_spike_stats(proj)
        self.rate_stats[s_type].add_items(spikes_per_second, 0, n_conns)
        self.total_weights[s_type] += spikes_per_tick * (w_max * n_conns)

    def __pre_spike_stats(self, proj):
        spikes_per_tick = max(
            1.0, self.default_spikes_per_second / self.steps_per_second)
        spikes_per_second = self.default_spikes_per_second
        # pylint: disable=protected-access
        pre_vertex = proj._projection_edge.pre_vertex
        if isinstance(pre_vertex, AbstractMaxSpikes):
            rate = pre_vertex.max_spikes_per_second()
            if rate != 0:
                spikes_per_second = rate
            spikes_per_tick = pre_vertex.max_spikes_per_ts()
        return spikes_per_tick, spikes_per_second

    def get_max_weight(self, s_type):
        if self.delay_running_totals[s_type].variance == 0.0:
            return max(self.total_weights[s_type], self.biggest_weight[s_type])

        stats = self.running_totals[s_type]
        rates = self.rate_stats[s_type]
        # pylint: disable=protected-access
        w_max = AbstractPopulationVertex._ring_buffer_expected_upper_bound(
            stats.mean, stats.standard_deviation, rates.mean,
            stats.n_items, self.ring_buffer_sigma)
        w_max = min(w_max, self.total_weights[s_type])
        w_max = max(w_max, self.biggest_weight[s_type])
        return w_max
