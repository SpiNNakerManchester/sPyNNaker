"""
Utilities for accessing the location of memory regions on the board
"""
from enum import Enum

# Some constants
SETUP_SIZE = 16  # Single word of info with flags, etc.
                 # plus the lengths of each of the output buffer
                 # regions in bytes

NO_PARAMS = 10
PARAMS_HEADER_SIZE = 3  # Number of 32-bit words in header of params block
PARAMS_BASE_SIZE = 4 * (PARAMS_HEADER_SIZE + NO_PARAMS)

RECORD_SPIKE_BIT = 1 << 0
RECORD_STATE_BIT = 1 << 1
RECORD_GSYN_BIT = 1 << 2

# From neuron common-typedefs.h
SYNAPSE_INDEX_BITS = 8
MAX_NEURON_SIZE = (1 << SYNAPSE_INDEX_BITS)
OUT_SPIKE_SIZE = (MAX_NEURON_SIZE >> 5)  # The size of each output spike line
OUT_SPIKE_BYTES = OUT_SPIKE_SIZE * 4  # The number of bytes for each spike line
V_BUFFER_SIZE_PER_TICK_PER_NEURON = 4
GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON = 4

INFINITE_SIMULATION = 4294967295

#natively supported delays for all models
MAX_SUPPORTED_DELAY_TICS = 16

DEFAULT_MASK = 0xfffff800  # DEFAULT LOCATION FOR THE APP MASK

#Model Names
APP_MONITOR_CORE_APPLICATION_ID = 0xAC0
IF_CURR_EXP_CORE_APPLICATION_ID = 0xAC1
SPIKESOURCEARRAY_CORE_APPLICATION_ID = 0xAC2
SPIKESOURCEPOISSON_CORE_APPLICATION_ID = 0xAC3
DELAY_EXTENSION_CORE_APPLICATION_ID = 0xAC4
ROBOT_MOTER_CONTROL_CORE_APPLICATION_ID = 0xAC5

REGIONS = enums.enum1(
    'SYSTEM',
    'NEURON_PARAMS',
    'SYNAPSE_PARAMS',
    'ROW_LEN_TRANSLATION',
    'MASTER_POP_TABLE',
    'SYNAPTIC_MATRIX',
    'STDP_PARAMS',
    'SPIKE_HISTORY',
    'POTENTIAL_HISTORY',
    'GSYN_HISTORY',
)

edges = enum0('EAST', 'NORTH_EAST', 'NORTH', 'WEST', 'SOUTH_WEST', 'SOUTH')