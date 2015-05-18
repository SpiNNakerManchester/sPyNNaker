"""
Utilities for accessing the location of memory regions on the board
"""
from enum import Enum

POSSION_SIGMA_SUMMATION_LIMIT = 3.0

BLOCK_INDEX_HEADER_WORDS = 3
BLOCK_INDEX_ROW_WORDS = 2

# database cap file path
MAX_DATABASE_PATH_LENGTH = 50000

RECORD_SPIKE_BIT = 1 << 0
RECORD_STATE_BIT = 1 << 1
RECORD_GSYN_BIT = 1 << 2
RECORDING_ENTRY_BYTE_SIZE = 4


# From neuron common-typedefs.h
SYNAPSE_INDEX_BITS = 8
MAX_NEURON_SIZE = (1 << SYNAPSE_INDEX_BITS)
OUT_SPIKE_SIZE = (MAX_NEURON_SIZE >> 5)  # The size of each output spike line
OUT_SPIKE_BYTES = OUT_SPIKE_SIZE * 4  # The number of bytes for each spike line
V_BUFFER_SIZE_PER_TICK_PER_NEURON = 4
GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON = 4

INFINITE_SIMULATION = 4294967295

# from synaptic manager
# Words - 2 for row lenth and number of rows and 1 for plastic region size
# (which might be 0)
SYNAPTIC_ROW_HEADER_WORDS = 2 + 1

NA_TO_PA_SCALE = 1000.0

# might not be used
WEIGHT_FLOAT_TO_FIXED_SCALE = 16.0
SCALE = WEIGHT_FLOAT_TO_FIXED_SCALE * NA_TO_PA_SCALE

# natively supported delays for all abstract_models
MAX_SUPPORTED_DELAY_TICS = 16
MAX_DELAY_BLOCKS = 8
MAX_TIMER_TICS_SUPPORTED_PER_BLOCK = 16

# debug filter positions
# multicast packets which are sent from a local chip where the local router has
# router entry for it (this is default routed to the monitor core which
# currently drops the packet).
MON_CORE_DEFAULT_RTD_PACKETS_FILTER_POSITION = 12

# input components
INPUT_CONDUCTANCE_COMPONENT_MAGIC_NUMBER = 0xAA1
INPUT_CURRENT_COMPONENT_MAGIC_NUMBER = 0xAA2

# model components
MODEL_COMPONENT_INTEGRATE_AND_FIRE_MAGIC_NUMBER = 0xAB1
MODEL_COMPONENT_IZHIKEVICH_MAGIC_NUMBER = 0xAB2

# synapse shaping magic numbers
SYNAPSE_SHAPING_ALPHA_MAGIC_NUMBER = 0xAC1
SYNAPSE_SHAPING_DELTA_MAGIC_NUMBER = 0xAC2
SYNAPSE_SHAPING_EXP_MAGIC_NUMBER = 0xAC3
SYNAPSE_SHAPING_DUEL_EXP_MAGIC_NUMBER = 0xAC4

# c main magic numbers
NEURON_MAGIC_NUMBER = 0xAD0
DELAY_MAGIC_NUMBER = 0xAD1
SPIKE_SOURCE_POISSON_MAGIC_NUMBER = 0xAD2
COMMAND_SENDER_MAGIC_NUMBER = 0xAD3
LIVE_PACKET_GATHERER_MAGIC_NUMBER = 0xAD4
REVERSE_IP_TAG_MULTICAST_SOURCE_MAGIC_NUMBER = 0xAD5
SPIKE_INJECTOR_MAGIC_NUMBER = 0xAD6
GRAPH_HEAT_ELEMENT_MAGIC_NUMBER = 0xAD8
GRAPH_CELL_ELEMENT_MAGIC_NUMBER = 0xAD9
GRAPH_PIXAL_ELEMENT_MAGIC_NUMBER = 0xADA

# master population table magic
MASTER_POP_2DARRAY_MAGIC_NUMBER = 0xBB1
MASTER_POP_BINARY_SEARCH_MAGIC_NUMBER = 0xBB2
MASTER_POP_HASH_TABLE_MAGIC_NUMBER = 0xBB3

# time dependancies magic numbers
TIME_DEPENDENCY_PFISTER_SPIKE_TRIPLET_MAGIC_NUMBER = 0xCC1
TIME_DEPENDENCY_SPIKE_PAIR_MAGIC_NUMBER = 0xCC2
TIME_DEPENDENCY_SPIKE_NEAREST_PAIR_MAGIC_NUMBER = 0xCC3

# weight dependancies magic numbers
WEIGHT_DEPENDENCY_ADDITIVE_MAGIC_NUMBER = 0xDD1
WEIGHT_DEPENDENCY_MULTIPLICATIVE_MAGIC_NUMBER = 0xDD2

# synapse structure magic numbers
SYNAPSE_PLASTIC_STRUCTURE_WEIGHT_CONTROL = 0xEE1
SYNAPSE_PLASTIC_STRUCTURE_WEIGHT = 0xEE2

# synpase dynamics magic numbers
SYNAPSE_DYNAMICS_STDP = 0xFF1
SYNAPSE_DYNAMICS_STDP_MAD = 0xFF2
SYNAPSE_DYNAMICS_STATIC = 0xFF3

# please see SpiNNFrontEndCommon/spinn_front_end_common/utilities/constants.py
# and sPyNNakerExtraModelsPlugin/spynnaker_extra_pynn_models/constants.py
# for other core application ids.
# or alterantively, look at :
# https://github.com/SpiNNakerManchester/SpiNNakerManchester.github.io/wiki/2015.005%3a-%22Arbitrary%22%3a-1.4%3a-Model-magic-numbers
# for a complete listing.

EDGES = Enum(
    value="EDGES",
    names=[("EAST", 0),
           ("NORTH_EAST", 1),
           ("NORTH", 2),
           ("WEST", 3),
           ("SOUTH_WEST", 4),
           ("SOUTH", 5)])

# Regions for populations
POPULATION_BASED_REGIONS = Enum(
    value="POPULATION_BASED_REGIONS",
    names=[("TIMINGS", 0),
           ('COMPONENTS', 1),
           ('RECORDING_REGION', 2),
           ('NEURON_PARAMS', 3),
           ('SYNAPSE_PARAMS', 4),
           ('POPULATION_TABLE', 5),
           ('SYNAPTIC_MATRIX', 6),
           ('SYNAPSE_DYNAMICS', 7),
           ('SPIKE_HISTORY', 8),
           ('POTENTIAL_HISTORY', 9),
           ('GSYN_HISTORY', 10)])

# The number of recording regions available for a population
N_POPULATION_RECORDING_REGIONS = 3

# The size of the headers of a population neuron region
# (1 word each for has_key, key, n_neurons, n_params, ODE timestep)
POPULATION_NEURON_PARAMS_HEADER_BYTES = 20

# The default routing mask to use
DEFAULT_MASK = 0xfffff800
