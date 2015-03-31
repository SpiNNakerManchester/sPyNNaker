"""
Utilities for accessing the location of memory regions on the board
"""
from enum import Enum
from spinn_front_end_common.utilities.constants import \
    DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS

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

# Model Names
IF_CURRENT_EXP_CORE_APPLICATION_ID = 0xAC1
SPIKESOURCEARRAY_CORE_APPLICATION_ID = 0xAC2
SPIKESOURCEPOISSON_CORE_APPLICATION_ID = 0xAC3
DELAY_EXTENSION_CORE_APPLICATION_ID = 0xAC4
MUNICH_MOTOR_CONTROL_CORE_APPLICATION_ID = 0xAC5
IF_CONDUCTIVE_EXP_CORE_APPLICATION_ID = 0xAC7
IZK_CURRENT_EXP_CORE_APPLICATION_ID = 0xAC8
# please see SpiNNFrontEndCommon/spinn_front_end_common/utilities/constants.py
# for other core application ids.

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
    names=[('SYSTEM', 0),
           ('NEURON_PARAMS', 1),
           ('SYNAPSE_PARAMS', 2),
           ('POPULATION_TABLE', 3),
           ('SYNAPTIC_MATRIX', 4),
           ('SYNAPSE_DYNAMICS', 5),
           ('SPIKE_HISTORY', 6),
           ('POTENTIAL_HISTORY', 7),
           ('GSYN_HISTORY', 8)])

# The number of recording regions available for a population
N_POPULATION_RECORDING_REGIONS = 3

# The size of the system region (+1 for flags) for a population
POPULATION_SYSTEM_REGION_BYTES = (DATA_SPECABLE_BASIC_SETUP_INFO_N_WORDS +
                                  N_POPULATION_RECORDING_REGIONS + 1) * 4

# The size of the headers of a population neuron region
# (1 word each for has_key, key, n_neurons, n_params, ODE timestep)
POPULATION_NEURON_PARAMS_HEADER_BYTES = 20

# The default routing mask to use
DEFAULT_MASK = 0xfffff800
