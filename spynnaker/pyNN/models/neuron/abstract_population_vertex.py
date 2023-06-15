# Copyright (c) 2015 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import math
import numpy
from scipy import special  # @UnresolvedImport
import operator
from functools import reduce
from collections import defaultdict

from pyNN.space import Grid2D, Grid3D
from pyNN.random import RandomDistribution

from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.ranged import RangeDictionary
from spinn_utilities.helpful_functions import is_singleton
from data_specification.enums.data_type import DataType
from spinn_utilities.config_holder import (
    get_config_int, get_config_float, get_config_bool)
from pacman.model.resources import MultiRegionSDRAM
from pacman.utilities.utility_calls import get_n_bits_for_fields, get_n_bits
from spinn_front_end_common.abstract_models import (
    AbstractCanReset)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, SYSTEM_BYTES_REQUIREMENT)
from spinn_front_end_common.interface.profiling.profile_utils import (
    get_profile_region_size)
from spinn_front_end_common.interface.buffer_management\
    .recording_utilities import (
       get_recording_header_size, get_recording_data_constant_size)
from spinn_front_end_common.interface.provenance import (
    ProvidesProvenanceDataFromMachineImpl)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.common import NeuronRecorder
from spynnaker.pyNN.models.abstract_models import (
    AbstractAcceptsIncomingSynapses, AbstractMaxSpikes, HasSynapses,
    SupportsStructure)
from spynnaker.pyNN.utilities.constants import (
    POSSION_SIGMA_SUMMATION_LIMIT)
from spynnaker.pyNN.utilities.running_stats import RunningStats
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSDRAMSynapseDynamics, AbstractSynapseDynamicsStructural,
    AbstractSupportsSignedWeights)
from spynnaker.pyNN.models.neuron.local_only import AbstractLocalOnly
from spynnaker.pyNN.models.neuron.synapse_dynamics import SynapseDynamicsStatic
from spynnaker.pyNN.utilities.utility_calls import (
    create_mars_kiss_seeds, check_rng)
from spynnaker.pyNN.utilities.bit_field_utilities import get_sdram_for_keys
from spynnaker.pyNN.utilities.struct import StructRepeat
from spynnaker.pyNN.models.common import (
    ParameterHolder, PopulationApplicationVertex)
from spynnaker.pyNN.models.common.param_generator_data import (
    MAX_PARAMS_BYTES, is_param_generatable)
from spynnaker.pyNN.exceptions import SpynnakerException
from spynnaker.pyNN.models.spike_source import SpikeSourcePoissonVertex
from .population_machine_neurons import PopulationMachineNeurons
from .synapse_io import get_max_row_info
from .master_pop_table import MasterPopTableAsBinarySearch
from .generator_data import GeneratorData
from .synaptic_matrices import SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES

logger = FormatAdapter(logging.getLogger(__name__))

# TODO: Make sure these values are correct (particularly CPU cycles)
_NEURON_BASE_DTCM_USAGE_IN_BYTES = 9 * BYTES_PER_WORD
_NEURON_BASE_N_CPU_CYCLES_PER_NEURON = 22
_NEURON_BASE_N_CPU_CYCLES = 10

_NEURON_GENERATOR_BASE_SDRAM = 12 * BYTES_PER_WORD
_NEURON_GENERATOR_PER_STRUCT = 4 * BYTES_PER_WORD
_NEURON_GENERATOR_PER_PARAM = 2 * BYTES_PER_WORD
_NEURON_GENERATOR_PER_ITEM = (2 * BYTES_PER_WORD) + MAX_PARAMS_BYTES

# 1 for number of neurons
# 1 for number of synapse types
# 1 for number of neuron bits
# 1 for number of synapse type bits
# 1 for number of delay bits
# 1 for drop late packets,
# 1 for incoming spike buffer size
_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES = 7 * BYTES_PER_WORD

_EXTRA_RECORDABLE_UNITS = {NeuronRecorder.SPIKES: "",
                           NeuronRecorder.PACKETS: "",
                           NeuronRecorder.REWIRING: ""}


def _prod(iterable):
    """
    Finds the product of the iterable.

    :param iterable iterable: Things to multiply together
    """
    return reduce(operator.mul, iterable, 1)


def _all_gen(rd):
    """
    Determine if all the values of a ranged dictionary can be generated.

    :rtype: bool
    """
    for key in rd.keys():
        if is_singleton(rd[key]):
            if not is_param_generatable(rd[key]):
                return False
        else:
            if not rd[key].range_based():
                return False
            for _start, _stop, val in rd[key].iter_ranges():
                if not is_param_generatable(val):
                    return False
    return True


def _check_random_dists(rd):
    """
    Check all RandomDistribution instances in a range dictionary to see if
    they have the rng value set.
    """
    for key in rd.keys():
        if is_singleton(rd[key]):
            if isinstance(rd[key], RandomDistribution):
                check_rng(rd[key].rng, f"RandomDistribtion for {key}")
        else:
            for _start, _stop, val in rd[key].iter_ranges():
                if isinstance(val, RandomDistribution):
                    check_rng(val.rng, f"RandomDistribution for {key}")


class AbstractPopulationVertex(
        PopulationApplicationVertex, AbstractAcceptsIncomingSynapses,
        AbstractCanReset, SupportsStructure):
    """
    Underlying vertex model for Neural Populations.
    Not actually abstract.
    """

    __slots__ = [
        "__incoming_spike_buffer_size",
        "__n_atoms",
        "__n_profile_samples",
        "__neuron_impl",
        "__neuron_recorder",
        "__synapse_recorder",
        "__parameters",
        "__pynn_model",
        "__state_variables",
        "__initial_state_variables",
        "__updated_state_variables",
        "__ring_buffer_sigma",
        "__spikes_per_second",
        "__drop_late_spikes",
        "__incoming_projections",
        "__incoming_poisson_projections",
        "__synapse_dynamics",
        "__max_row_info",
        "__self_projection",
        "__current_sources",
        "__current_source_id_list",
        "__structure",
        "__rng",
        "__pop_seed",
        "__core_seeds",
        "__connection_cache",
        "__read_initial_values",
        "__have_read_initial_values",
        "__last_parameter_read_time",
        "__n_colour_bits"]

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

    # Elements before the start of global parameters
    # 1. has key, 2. key, 3. n atoms, 4. n_atoms_peak 5. n_colour_bits
    CORE_PARAMS_BASE_SIZE = 5 * BYTES_PER_WORD

    def __init__(
            self, n_neurons, label, max_atoms_per_core,
            spikes_per_second, ring_buffer_sigma, incoming_spike_buffer_size,
            neuron_impl, pynn_model, drop_late_spikes, splitter, seed,
            n_colour_bits):
        """
        :param int n_neurons: The number of neurons in the population
        :param str label: The label on the population
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
        :type splitter:
            ~pacman.model.partitioner_splitters.AbstractSplitterCommon or None
        :param seed:
            The Population seed, used to ensure the same random generation
            on each run.
        :param int n_colour_bits: The number of colour bits to use
        """
        # pylint: disable=too-many-arguments
        super().__init__(label, max_atoms_per_core, splitter)

        self.__n_atoms = self.round_n_atoms(n_neurons, "n_neurons")

        # buffer data
        self.__incoming_spike_buffer_size = incoming_spike_buffer_size

        if incoming_spike_buffer_size is None:
            self.__incoming_spike_buffer_size = get_config_int(
                "Simulation", "incoming_spike_buffer_size")

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
        self.__parameters = RangeDictionary(n_neurons)
        self.__neuron_impl.add_parameters(self.__parameters)
        self.__initial_state_variables = RangeDictionary(n_neurons)
        self.__neuron_impl.add_state_variables(self.__initial_state_variables)
        self.__state_variables = self.__initial_state_variables.copy()
        self.__n_colour_bits = n_colour_bits
        if self.__n_colour_bits is None:
            self.__n_colour_bits = get_config_int(
                "Simulation", "n_colour_bits")

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

        # Current sources for this vertex
        self.__current_sources = []
        self.__current_source_id_list = dict()

        # Set up for profiling
        self.__n_profile_samples = get_config_int(
            "Reports", "n_profile_samples")

        # Set up for incoming
        self.__incoming_projections = defaultdict(list)
        self.__incoming_poisson_projections = list()
        self.__max_row_info = dict()
        self.__self_projection = None

        # Keep track of the synapse dynamics for the vertex overall
        self.__synapse_dynamics = SynapseDynamicsStatic()

        self.__structure = None

        # An RNG for use in synaptic generation
        self.__rng = numpy.random.RandomState(seed)
        self.__pop_seed = create_mars_kiss_seeds(self.__rng)
        self.__core_seeds = dict()

        # Store connections read from machine until asked to clear
        # Key is app_edge, synapse_info
        self.__connection_cache = dict()
        self.__read_initial_values = False
        self.__have_read_initial_values = False
        self.__last_parameter_read_time = None

    @overrides(PopulationApplicationVertex.get_max_atoms_per_core)
    def get_max_atoms_per_core(self):
        max_atoms = super().get_max_atoms_per_core()

        # Dynamically adjust depending on the needs of the synapse dynamics
        return min(
            max_atoms, self.__synapse_dynamics.absolute_max_atoms_per_core)

    @overrides(
        PopulationApplicationVertex.get_max_atoms_per_dimension_per_core)
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
                "When using a multidimensional Population, a maximum number of"
                " neurons per core for each dimension must be provided such"
                " that the total number of neurons per core is less than or"
                f" equal to {max_atoms}")
        if len(max_per_dim) != len(self.atoms_shape):
            raise SpynnakerException(
                "When using a multidimensional Population, a maximum number of"
                " neurons per core must be provided for each dimension (in"
                " this case, please set a max neurons per core with"
                f" {len(self.atoms_shape)} dimensions)")
        return max_per_dim

    @overrides(PopulationApplicationVertex.
               set_max_atoms_per_dimension_per_core)
    def set_max_atoms_per_dimension_per_core(self, new_value):
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
    def combined_core_capable(self):
        """
        Whether the vertex can manage to operate on a combined
        neuron-synapse core, or if a split synapse-core is more
        appropriate.

        .. note::
            This is currently based only on the ITCM available, not
            on the incoming synapses, but could be combined with
            n_synapse_cores_required to determine if, and how-many, synapse
            cores are needed.

        :rtype: bool
        """
        if self.__synapse_dynamics is None:
            return True
        return self.__synapse_dynamics.is_combined_core_capable

    @property
    def n_synapse_cores_required(self):
        """
        The estimated number of synapse cores required, when using a
        split synapse-neuron core model.

        .. note::
            This is currently hard-coded but could be updated to work
            this out based on the number of incoming synapses.

        :rtype: int
        """
        return 1

    @property
    def synapse_dynamics(self):
        """
        The synapse dynamics used by the synapses e.g. plastic or static.
        Settable.

        :rtype: AbstractSynapseDynamics or None
        """
        return self.__synapse_dynamics

    @synapse_dynamics.setter
    def synapse_dynamics(self, synapse_dynamics):
        """
        Set the synapse dynamics.

        .. note::
            After setting, the dynamics might not be the type set as it can
            be combined with the existing dynamics in exciting ways.

        :param AbstractSynapseDynamics synapse_dynamics:
            The synapse dynamics to set
        """
        self.__synapse_dynamics = self.__synapse_dynamics.merge(
            synapse_dynamics)

    def add_incoming_projection(self, projection):
        """
        Add a projection incoming to this vertex.

        :param ~spynnaker.pyNN.models.projection.Projection projection:
            The new projection to add
        """
        # Reset the ring buffer shifts as a projection has been added
        SpynnakerDataView.set_requires_mapping()
        self.__max_row_info.clear()
        # pylint: disable=protected-access
        pre_vertex = projection._projection_edge.pre_vertex
        self.__incoming_projections[pre_vertex].append(projection)
        if pre_vertex == self:
            self.__self_projection = projection
        if isinstance(pre_vertex, SpikeSourcePoissonVertex):
            self.__incoming_poisson_projections.append(projection)

    @property
    def self_projection(self):
        """
        Any projection from this vertex to itself.

        :rtype: ~spynnaker.pyNN.models.projection.Projection or None
        """
        return self.__self_projection

    @property
    @overrides(PopulationApplicationVertex.n_atoms)
    def n_atoms(self):
        return self.__n_atoms

    @property
    @overrides(PopulationApplicationVertex.atoms_shape)
    def atoms_shape(self):
        if isinstance(self.__structure, (Grid2D, Grid3D)):
            return self.__structure.calculate_size(self.__n_atoms)
        return super(AbstractPopulationVertex, self).atoms_shape

    @property
    def size(self):
        """
        The number of neurons in the vertex.

        :rtype: int
        """
        return self.__n_atoms

    @property
    def incoming_spike_buffer_size(self):
        """
        The size of the incoming spike buffer to be used on the cores.

        :rtype: int
        """
        return self.__incoming_spike_buffer_size

    @property
    def parameters(self):
        """
        The parameters of the neurons in the population.

        :rtype: ~spinn_utilities.ranged.RangeDictionary
        """
        return self.__parameters

    @property
    def state_variables(self):
        """
        The state variables of the neuron in the population.

        :rtype: ~spinn_utilities.ranged.RangeDicationary
        """
        return self.__state_variables

    @property
    def initial_state_variables(self):
        """
        The initial values of the state variables of the neurons.

        :rtype: ~spinn_utilities.ranged.RangeDictionary
        """
        return self.__initial_state_variables

    @property
    def neuron_impl(self):
        """
        The neuron implementation.

        :rtype: AbstractNeuronImpl
        """
        return self.__neuron_impl

    @property
    def n_profile_samples(self):
        """
        The maximum number of profile samples to report.

        :rtype: int
        """
        return self.__n_profile_samples

    @property
    def neuron_recorder(self):
        """
        The recorder for neurons.

        :rtype: NeuronRecorder
        """
        return self.__neuron_recorder

    @property
    def synapse_recorder(self):
        """
        The recorder for synapses.

        :rtype: SynapseRecorder
        """
        return self.__synapse_recorder

    @property
    def drop_late_spikes(self):
        """
        Whether spikes should be dropped if not processed in a timestep.

        :rtype: bool
        """
        return self.__drop_late_spikes

    def get_sdram_usage_for_core_neuron_params(self, n_atoms):
        """
        :param int n_atoms: The number of atoms per core
        :return: The SDRAM required for the core neuron parameters
        :rtype: int
        """
        return (
            self.CORE_PARAMS_BASE_SIZE +
            (self.__neuron_impl.get_n_synapse_types() * BYTES_PER_WORD) +
            # The keys per neuron
            n_atoms * BYTES_PER_WORD)

    def get_sdram_usage_for_neuron_params(self, n_atoms):
        """
        Calculate the SDRAM usage for just the neuron parameters region.

        :param int n_atoms: The number of atoms per core
        :return: The SDRAM required for the neuron region
        :rtype: int
        """
        return sum(s.get_size_in_whole_words(n_atoms)
                   if s.repeat_type == StructRepeat.PER_NEURON
                   else s.get_size_in_whole_words()
                   for s in self.__neuron_impl.structs) * BYTES_PER_WORD

    def get_sdram_usage_for_neuron_generation(self, n_atoms):
        """
        Calculate the SDRAM usage for the neuron generation region.

        :param int n_atoms: The number of atoms per core
        :return: The SDRAM required for the neuron generator region
        :rtype: int
        """
        return (self.__get_sdram_usage_for_neuron_struct_generation(n_atoms) +
                self.__neuron_recorder.get_generator_sdram_usage_in_bytes(
                    n_atoms))

    def __get_sdram_usage_for_neuron_struct_generation(self, n_atoms):
        """
        Calculate the SDRAM usage for the neuron struct generation region.

        :param int n_atoms: The number of atoms per core
        :return: The SDRAM required for the neuron generator region
        :rtype: int
        """
        # Uses nothing if not generatable
        structs = self.__neuron_impl.structs
        for struct in structs:
            if not struct.is_generatable:
                return 0

        # If structs are generatable, we can guess that parameters are,
        # and then assume each parameter is different for maximum SDRAM.
        n_structs = len(structs)
        n_params = sum(len(s.fields) for s in structs)
        return sum([
            _NEURON_GENERATOR_BASE_SDRAM,
            _NEURON_GENERATOR_PER_STRUCT * n_structs,
            _NEURON_GENERATOR_PER_PARAM * n_params,
            _NEURON_GENERATOR_PER_ITEM * n_params * n_atoms
        ])

    def get_sdram_usage_for_current_source_params(self, n_atoms):
        """
        Calculate the SDRAM usage for the current source parameters region.

        :param int n_atoms: The number of atoms to account for
        :return: The SDRAM required for the current source region
        :rtype: int
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

    def __read_parameters_now(self):
        # If we already read the parameters at this time, don't do it again
        current_time = SpynnakerDataView().get_current_run_time_ms()
        if self.__last_parameter_read_time == current_time:
            return

        self.__last_parameter_read_time = current_time
        for m_vertex in self.machine_vertices:
            if isinstance(m_vertex, PopulationMachineNeurons):
                placement = SpynnakerDataView.get_placement_of_vertex(m_vertex)
                m_vertex.read_parameters_from_machine(placement)

    def __read_initial_parameters_now(self):
        # If we already read the initial parameters, don't do it again
        if self.__have_read_initial_values:
            return

        for m_vertex in self.machine_vertices:
            if isinstance(m_vertex, PopulationMachineNeurons):
                placement = SpynnakerDataView.get_placement_of_vertex(m_vertex)
                m_vertex.read_initial_parameters_from_machine(placement)

    def __read_parameter(self, name, selector=None):
        return self.__parameters[name].get_values(selector)

    @overrides(PopulationApplicationVertex.get_parameter_values)
    def get_parameter_values(self, names, selector=None):
        self._check_parameters(names, set(self.__parameters.keys()))
        # If we haven't yet run, or have just reset, note to read the values
        # when they are ready
        if not SpynnakerDataView.is_ran_last():
            self.__read_initial_values = True
        elif SpynnakerDataView.has_transceiver():
            self.__read_parameters_now()
        return ParameterHolder(names, self.__read_parameter, selector)

    @overrides(PopulationApplicationVertex.set_parameter_values)
    def set_parameter_values(self, name, value, selector=None):
        # If we have run, and not reset, we need to read the values back
        # so that we don't overwrite the state.  Note that a reset will
        # then make this a waste, but we can't see the future...
        if SpynnakerDataView.is_ran_last():
            self.__read_parameters_now()
            self.__tell_neuron_vertices_to_regenerate()
        self.__parameters[name].set_value_by_selector(selector, value)

    @overrides(PopulationApplicationVertex.get_parameters)
    def get_parameters(self):
        return self.__pynn_model.default_parameters.keys()

    def __read_initial_state_variable(self, name, selector=None):
        return self.__initial_state_variables[name].get_values(selector)

    @overrides(PopulationApplicationVertex.get_initial_state_values)
    def get_initial_state_values(self, names, selector=None):
        self._check_variables(names, set(self.__state_variables.keys()))
        # If we haven't yet run, or have just reset, note to read the values
        # when they are ready
        if not SpynnakerDataView.is_ran_last():
            self.__read_initial_values = True
        else:
            self.__read_initial_parameters_now()
        return ParameterHolder(
            names, self.__read_initial_state_variable, selector)

    @overrides(PopulationApplicationVertex.set_initial_state_values)
    def set_initial_state_values(self, name, value, selector=None):
        self._check_variables([name], set(self.__state_variables.keys()))
        if not SpynnakerDataView.is_ran_last():
            self.__state_variables[name].set_value_by_selector(
                selector, value)
        self.__initial_state_variables[name].set_value_by_selector(
            selector, value)

    def __read_current_state_variable(self, name, selector=None):
        return self.__state_variables[name].get_values(selector)

    @overrides(PopulationApplicationVertex.get_current_state_values)
    def get_current_state_values(self, names, selector=None):
        self._check_variables(names, set(self.__state_variables.keys()))
        # If we haven't yet run, or have just reset, note to read the values
        # when they are ready
        if not SpynnakerDataView.is_ran_last():
            self.__read_initial_values = True
        else:
            self.__read_parameters_now()
        return ParameterHolder(
            names, self.__read_current_state_variable, selector)

    @overrides(PopulationApplicationVertex.set_current_state_values)
    def set_current_state_values(self, name, value, selector=None):
        self._check_variables([name], set(self.__state_variables.keys()))
        # If we have run, and not reset, we need to read the values back
        # so that we don't overwrite all the state.  Note that a reset will
        # then make this a waste, but we can't see the future...
        if SpynnakerDataView.is_ran_last():
            self.__read_parameters_now()
            self.__tell_neuron_vertices_to_regenerate()
        self.__state_variables[name].set_value_by_selector(
            selector, value)

    @overrides(PopulationApplicationVertex.get_state_variables)
    def get_state_variables(self):
        return self.__pynn_model.default_initial_values.keys()

    @overrides(PopulationApplicationVertex.get_units)
    def get_units(self, name):
        if name in _EXTRA_RECORDABLE_UNITS:
            return _EXTRA_RECORDABLE_UNITS[name]
        if self.__neuron_impl.is_recordable(name):
            return self.__neuron_impl.get_recordable_units(name)
        if (name not in self.__parameters and
                name not in self.__state_variables):
            raise KeyError(f"No such parameter {name}")
        return self.__neuron_impl.get_units(name)

    @property
    @overrides(PopulationApplicationVertex.conductance_based)
    def conductance_based(self):
        return self.__neuron_impl.is_conductance_based

    @overrides(PopulationApplicationVertex.get_recordable_variables)
    def get_recordable_variables(self):
        variables = list()
        variables.extend(self.__neuron_recorder.get_recordable_variables())
        variables.extend(self.__synapse_recorder.get_recordable_variables())
        return variables

    @overrides(PopulationApplicationVertex.get_buffer_data_type)
    def get_buffer_data_type(self, name):
        if self.__neuron_recorder.is_recordable(name):
            return self.__neuron_recorder.get_buffer_data_type(name)
        if self.__synapse_recorder.is_recordable(name):
            return self.__synapse_recorder.get_buffer_data_type(name)
        raise KeyError(f"It is not possible to record {name}")

    @overrides(PopulationApplicationVertex.set_recording)
    def set_recording(self, name, sampling_interval=None, indices=None):
        if self.__neuron_recorder.is_recordable(name):
            self.__neuron_recorder.set_recording(
                name, True, sampling_interval, indices)
        elif self.__synapse_recorder.is_recordable(name):
            self.__synapse_recorder.set_recording(
                name, True, sampling_interval, indices)
        else:
            raise KeyError(f"It is not possible to record {name}")
        SpynnakerDataView.set_requires_mapping()

    @overrides(PopulationApplicationVertex.set_not_recording)
    def set_not_recording(self, name, indices=None):
        if self.__neuron_recorder.is_recordable(name):
            self.__neuron_recorder.set_recording(name, False, indexes=indices)
        elif self.__synapse_recorder.is_recordable(name):
            self.__synapse_recorder.set_recording(name, False, indexes=indices)
        else:
            raise KeyError(f"It is not possible to record {name}")

    @overrides(PopulationApplicationVertex.get_recording_variables)
    def get_recording_variables(self):
        recording = list()
        recording.extend(self.__neuron_recorder.recording_variables)
        recording.extend(self.__synapse_recorder.recording_variables)
        return recording

    @overrides(PopulationApplicationVertex.get_sampling_interval_ms)
    def get_sampling_interval_ms(self, name):
        if self.__neuron_recorder.is_recordable(name):
            return self.__neuron_recorder.get_sampling_interval_ms(name)
        if self.__synapse_recorder.is_recordable(name):
            return self.__synapse_recorder.get_sampling_interval_ms(name)
        raise KeyError(f"It is not possible to record {name}")

    @overrides(PopulationApplicationVertex.get_data_type)
    def get_data_type(self, name):
        if self.__neuron_recorder.is_recordable(name):
            return self.__neuron_recorder.get_data_type(name)
        if self.__synapse_recorder.is_recordable(name):
            return self.__synapse_recorder.get_data_type(name)
        raise KeyError(f"It is not possible to record {name}")

    @overrides(PopulationApplicationVertex.get_recording_region)
    def get_recording_region(self, name):
        if self.__neuron_recorder.is_recordable(name):
            return self.__neuron_recorder.get_region(name)
        if self.__synapse_recorder.is_recordable(name):
            return self.__synapse_recorder.get_region(name)
        raise KeyError(f"It is not possible to record {name}")

    @overrides(PopulationApplicationVertex.get_neurons_recording)
    def get_neurons_recording(self, name, vertex_slice):
        if self.__neuron_recorder.is_recordable(name):
            return self.__neuron_recorder.neurons_recording(
                name, vertex_slice)
        if self.__synapse_recorder.is_recordable(name):
            return self.__synapse_recorder.neurons_recording(
                name, vertex_slice)
        raise KeyError(f"It is not possible to record {name}")

    @property
    def weight_scale(self):
        """
        :rtype: float
        """
        return self.__neuron_impl.get_global_weight_scale()

    @property
    def ring_buffer_sigma(self):
        """
        :rtype: float
        """
        return self.__ring_buffer_sigma

    @ring_buffer_sigma.setter
    def ring_buffer_sigma(self, ring_buffer_sigma):
        self.__ring_buffer_sigma = ring_buffer_sigma

    @property
    def spikes_per_second(self):
        """
        :rtype: float
        """
        return self.__spikes_per_second

    @spikes_per_second.setter
    def spikes_per_second(self, spikes_per_second):
        self.__spikes_per_second = spikes_per_second

    def set_synapse_dynamics(self, synapse_dynamics):
        """
        Set the synapse dynamics of this population.

        :param AbstractSynapseDynamics synapse_dynamics:
            The synapse dynamics to set
        """
        self.synapse_dynamics = synapse_dynamics

    def clear_connection_cache(self):
        """
        Flush the cache of connection information; needed for a second run.
        """
        self.__connection_cache.clear()

    def describe(self):
        """
        Get a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see :py:mod:`pyNN.descriptions`).

        If template is `None`, then a dictionary containing the template
        context will be returned.

        :rtype: dict(str, any)
        """
        parameters = dict(self.get_parameter_values(
            self.__pynn_model.default_parameters.keys()))

        context = {
            "name": self.__neuron_impl.model_name,
            "default_parameters": self.__pynn_model.default_parameters,
            "default_initial_values": self.__pynn_model.default_parameters,
            "parameters": parameters,
        }
        return context

    def get_synapse_id_by_target(self, target):
        """
        Get the id of synapse using its target name.

        :param str target: The synapse to get the id of
        :rtype: int
        """
        return self.__neuron_impl.get_synapse_id_by_target(target)

    @overrides(PopulationApplicationVertex.inject)
    def inject(self, current_source, selector=None):
        self.__current_sources.append(current_source)
        self.__current_source_id_list[current_source] = selector
        # set the associated vertex (for multi-run case)
        current_source.set_app_vertex(self)
        # set to reload for multi-run case
        for m_vertex in self.machine_vertices:
            m_vertex.set_reload_required(True)

    @property
    def current_sources(self):
        """
        Current sources needed to be available to machine vertex.

        :rtype: list(AbstractCurrentSource)
        """
        return self.__current_sources

    @property
    def current_source_id_list(self):
        """
        Current source ID list needed to be available to machine vertex.

        :rtype: dict(AbstractCurrentSource,any)
        """
        return self.__current_source_id_list

    def __str__(self):
        return f"{self.label} with {self.n_atoms} atoms"

    def __repr__(self):
        return self.__str__()

    @overrides(AbstractCanReset.reset_to_first_timestep)
    def reset_to_first_timestep(self):
        # Reset state variables
        self.__state_variables.copy_into(self.__initial_state_variables)

        # If synapses change during the run also regenerate these to get
        # back to the initial state
        if self.__synapse_dynamics.changes_during_run:
            SpynnakerDataView.set_requires_data_generation()
        else:
            # We only get neuron vertices to regenerate not redoing data
            # generation
            self.__tell_neuron_vertices_to_regenerate()

    @staticmethod
    def _ring_buffer_expected_upper_bound(
            weight_mean, weight_std_dev, spikes_per_second,
            n_synapses_in, sigma):
        """
        Provides expected upper bound on accumulated values in a ring
        buffer element.

        Requires an assessment of maximum Poisson input rate.

        Assumes knowledge of mean and SD of weight distribution, fan-in
        and timestep.

        All arguments should be assumed real values except n_synapses_in
        which will be an integer.

        :param float weight_mean: Mean of weight distribution (in either nA or
            microSiemens as required)
        :param float weight_std_dev: SD of weight distribution
        :param float spikes_per_second: Maximum expected Poisson rate in Hz
        :param int machine_timestep: in us
        :param int n_synapses_in: No of connected synapses
        :param float sigma: How many SD above the mean to go for upper bound;
            a good starting choice is 5.0. Given length of simulation we can
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
        """
        Get the shift of the ring buffers for transfer of values into the
        input buffers for this model.

        :param incoming_projections:
            The projections to consider in the calculations
        :type incoming_projections:
            list(~spynnaker.pyNN.models.projection.Projection)
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
        """
        Return the amount to scale the weights by to convert them from
        floating point values to 16-bit fixed point numbers which can be
        shifted left by ring_buffer_to_input_left_shift to produce an
        s1615 fixed point number.

        :param int ring_buffer_to_input_left_shift:
        :rtype: float
        """
        return float(math.pow(2, 16 - (ring_buffer_to_input_left_shift + 1)))

    def get_weight_scales(self, ring_buffer_shifts):
        """
        Get the weight scaling to apply to weights in synapses.

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
        # If we already have connections cached, return them
        if (app_edge, synapse_info) in self.__connection_cache:
            return self.__connection_cache[app_edge, synapse_info]

        # Start with something in the list so that concatenate works
        connections = [numpy.zeros(
                0, dtype=AbstractSDRAMSynapseDynamics.NUMPY_CONNECTORS_DTYPE)]
        progress = ProgressBar(
            len(self.machine_vertices),
            f"Getting synaptic data between {app_edge.pre_vertex.label} "
            f"and {app_edge.post_vertex.label}")
        for post_vertex in progress.over(self.machine_vertices):
            if isinstance(post_vertex, HasSynapses):
                placement = SpynnakerDataView.get_placement_of_vertex(
                    post_vertex)
                connections.extend(post_vertex.get_connections_from_machine(
                    placement, app_edge, synapse_info))
        all_connections = numpy.concatenate(connections)
        self.__connection_cache[app_edge, synapse_info] = all_connections
        return all_connections

    def get_synapse_params_size(self):
        """
        Get the size of the synapse parameters, in bytes.

        :rtype: int
        """
        # This will only hold ring buffer scaling for the neuron synapse
        # types
        return (_SYNAPSES_BASE_SDRAM_USAGE_IN_BYTES +
                (BYTES_PER_WORD * self.__neuron_impl.get_n_synapse_types()))

    def get_synapse_dynamics_size(self, n_atoms):
        """
        Get the size of the synapse dynamics region, in bytes.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of the vertex to get the usage of
        :rtype: int
        """
        if isinstance(self.__synapse_dynamics, AbstractLocalOnly):
            return self.__synapse_dynamics.get_parameters_usage_in_bytes(
                self.incoming_projections)

        return self.__synapse_dynamics.get_parameters_sdram_usage_in_bytes(
            n_atoms, self.__neuron_impl.get_n_synapse_types())

    def get_structural_dynamics_size(self, n_atoms):
        """
        Get the size of the structural dynamics region, in bytes.

        :param int n_atoms:
            The number of atoms in the slice
        :rtype: int
        """
        if not isinstance(
                self.__synapse_dynamics, AbstractSynapseDynamicsStructural):
            return 0

        return self.__synapse_dynamics\
            .get_structural_parameters_sdram_usage_in_bytes(
                self.incoming_projections, n_atoms)

    def get_synapses_size(self, n_post_atoms):
        """
        Get the maximum SDRAM usage for the synapses on a vertex slice.

        :param int n_post_atoms: The number of atoms projected to
        :param incoming_projections:
            The projections to consider in the calculations
        :type incoming_projections:
            list(~spynnaker.pyNN.models.projection.Projection)
        :rtype: int
        """
        if isinstance(self.__synapse_dynamics, AbstractLocalOnly):
            return 0
        addr = 2 * BYTES_PER_WORD
        for proj in self.incoming_projections:
            addr = self.__add_matrix_size(addr, proj, n_post_atoms)
        return addr

    def __add_matrix_size(self, addr, projection, n_post_atoms):
        """
        Add to the address the size of the matrices for the projection to
        the vertex slice.

        :param int addr: The address to start from
        :param ~spynnaker.pyNN.models.projection.Projection:
            The projection to add
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
        """
        Get maximum row length data.

        :param SynapseInformation synapse_info: Information about synapses
        :param int n_post_atoms: The number of atoms projected to
        :param ProjectionApplicationEdge app_edge: The edge of the projection
        :rtype: MaxRowInfo
        """
        key = (app_edge, synapse_info, n_post_atoms)
        if key in self.__max_row_info:
            return self.__max_row_info[key]
        max_row_info = get_max_row_info(
            synapse_info, n_post_atoms, app_edge.n_delay_stages, app_edge)
        self.__max_row_info[key] = max_row_info
        return max_row_info

    def get_synapse_expander_size(self):
        """
        Get the size of the synapse expander region, in bytes.

        :rtype: int
        """
        size = SYNAPSES_BASE_GENERATOR_SDRAM_USAGE_IN_BYTES
        size += (self.__neuron_impl.get_n_synapse_types() *
                 DataType.U3232.size)
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
        size += get_sdram_for_keys(self.incoming_projections)
        return size

    @staticmethod
    def __generator_info_size(synapse_info):
        """
        The number of bytes required by the generator information.

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
        """
        The suffix of the executable name due to the type of synapses in use.

        :rtype: str
        """
        return self.__synapse_dynamics.get_vertex_executable_suffix()

    @property
    def neuron_recordables(self):
        """
        The names of variables that can be recorded by the neuron.

        :rtype: list(str)
        """
        return self.__neuron_recorder.get_recordable_variables()

    @property
    def synapse_recordables(self):
        """
        The names of variables that can be recorded by the synapses.

        :rtype: list(str)
        """
        return self.__synapse_recorder.get_recordable_variables()

    def get_common_constant_sdram(
            self, n_record, n_provenance, common_regions):
        """
        Get the amount of SDRAM used by common parts.

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
        """
        Get the amount of SDRAM per timestep used by neuron parts.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of
        :rtype: int
        """
        return self.__neuron_recorder.get_variable_sdram_usage(vertex_slice)

    def get_max_neuron_variable_sdram(self, n_neurons):
        """
        Get the amount of SDRAM per timestep used by neuron parts.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of
        :rtype: int
        """
        return self.__neuron_recorder.get_max_variable_sdram_usage(n_neurons)

    def get_synapse_variable_sdram(self, vertex_slice):
        """
        Get the amount of SDRAM per timestep used by synapse parts.

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
        """
        Get the amount of SDRAM per timestep used by synapse parts.

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
        """
        Get the amount of fixed SDRAM used by neuron parts.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice of neurons to get the size of
        :param NeuronRegions neuron_regions: Region IDs
        :rtype: int
        """
        params_cost = self.get_sdram_usage_for_neuron_params(n_atoms)
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            neuron_regions.core_params,
            self.get_sdram_usage_for_core_neuron_params(n_atoms))
        sdram.add_cost(neuron_regions.neuron_params, params_cost)
        sdram.add_cost(
            neuron_regions.current_source_params,
            self.get_sdram_usage_for_current_source_params(n_atoms))
        sdram.add_cost(
            neuron_regions.neuron_recording,
            self.__neuron_recorder.get_metadata_sdram_usage_in_bytes(
                n_atoms))
        sdram.add_cost(
            neuron_regions.neuron_builder,
            self.get_sdram_usage_for_neuron_generation(n_atoms))
        sdram.add_cost(neuron_regions.initial_values, params_cost)
        return sdram

    @property
    def incoming_projections(self):
        """
        The projections that target this population vertex.

        :rtype: iterable(~spynnaker.pyNN.models.projection.Projection)
        """
        for proj_list in self.__incoming_projections.values():
            for proj in proj_list:
                yield proj

    def get_incoming_projections_from(self, source_vertex):
        """
        The projections that target this population vertex from
        the given source.

        :rtype: iterable(~spynnaker.pyNN.models.projection.Projection)
        """
        return self.__incoming_projections[source_vertex]

    @property
    def incoming_poisson_projections(self):
        """
        The projections that target this population vertex which
        originate from a Poisson source.

        :rtype: iterable(~spynnaker.pyNN.models.projection.Projection)
        """
        return self.__incoming_poisson_projections

    @property
    def pop_seed(self):
        """
        The seed to use for the population overall; a list of four integers.

        :rtype: list(int)
        """
        return self.__pop_seed

    def core_seed(self, vertex_slice):
        """
        The seed to use for a core.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The machine vertex that the seed is for
        :return: A list of 4 integers
        :rtype: list(int)
        """
        if vertex_slice not in self.__core_seeds:
            self.__core_seeds[vertex_slice] = create_mars_kiss_seeds(
                self.__rng)
        return self.__core_seeds[vertex_slice]

    def copy_initial_state_variables(self, vertex_slice):
        """
        Copies the state variables into the initial state variables.

        :param ~pacman.model.graphs.common.Slice vertex_slice:
            The slice to copy now
        """
        for key in self.__state_variables.keys():
            value = self.__state_variables[key][vertex_slice.as_slice]
            self.__initial_state_variables[key].set_value_by_slice(
                vertex_slice.lo_atom, vertex_slice.hi_atom + 1, value)
        # This is called during reading of initial values, so we don't
        # need to do it again
        self.__read_initial_values = False
        self.__have_read_initial_values = True

    @property
    def read_initial_values(self):
        """
        Whether initial values need to be stored.

        :rtype: bool
        """
        return self.__read_initial_values

    def __tell_neuron_vertices_to_regenerate(self):
        for vertex in self.machine_vertices:
            if isinstance(vertex, PopulationMachineNeurons):
                vertex.set_do_neuron_regeneration()

    @property
    @overrides(PopulationApplicationVertex.n_colour_bits)
    def n_colour_bits(self):
        return self.__n_colour_bits

    def get_max_delay(self, max_ring_buffer_bits):
        """
        Get the maximum delay and whether a delay extension is needed
        for a given maximum number of ring buffer bits.

        :param int max_ring_buffer_bits:
            The maximum number of bits that can be used for the ring buffer
            identifier (i.e. delay, synapse type, neuron index)
        :return:
            Tuple of the maximum delay supported on the core and whether
            a delay extension is needed to support delays
        :rtype: tuple(int, bool)
        """
        # Find the maximum delay from incoming synapses
        max_delay_ms = 0
        for proj in self.incoming_projections:
            # pylint: disable=protected-access
            s_info = proj._synapse_information
            proj_max_delay = s_info.synapse_dynamics.get_delay_maximum(
                s_info.connector, s_info)
            max_delay_ms = max(max_delay_ms, proj_max_delay)
        max_delay_steps = math.ceil(
            max_delay_ms / SpynnakerDataView.get_simulation_time_step_ms())
        max_delay_bits = get_n_bits(max_delay_steps)

        # Find the maximum possible delay
        n_atom_bits = self.get_n_atom_bits()
        n_synapse_bits = get_n_bits(
            self.neuron_impl.get_n_synapse_types())
        n_delay_bits = max_ring_buffer_bits - (n_atom_bits + n_synapse_bits)

        # Pick the smallest between the two, so that not too many bits are used
        final_n_delay_bits = min(n_delay_bits, max_delay_bits)
        return 2 ** final_n_delay_bits, max_delay_bits > final_n_delay_bits

    def get_n_atom_bits(self):
        """
        :rtype: int
        """
        field_sizes = [
            min(max_atoms, n) for max_atoms, n in zip(
                self.get_max_atoms_per_dimension_per_core(), self.atoms_shape)]
        return get_n_bits_for_fields(field_sizes)

    def can_generate_on_machine(self):
        """
        Determine if the parameters of this vertex can be generated on the
        machine

        :rtype: bool
        """

        # Check that all the structs can actually be generated
        for struct in self.__neuron_impl.structs:
            if not struct.is_generatable:
                # If this is false, we can't generate anything on machine
                return False

        if (not _all_gen(self.__parameters) or
                not _all_gen(self.__state_variables)):
            return False

        _check_random_dists(self.__parameters)
        _check_random_dists(self.__state_variables)
        return True


class _Stats(object):
    """
    Object to keep hold of and process statistics for ring buffer scaling.
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
