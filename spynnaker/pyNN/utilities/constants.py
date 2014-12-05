"""
Utilities for accessing the location of memory regions on the board
"""
from enum import Enum

POSSION_SIGMA_SUMMATION_LIMIT = 3.0
# Some constants
SETUP_SIZE = 28  # Single word of info with flags, etc.
                 # plus the lengths of each of the output buffer
                 # regions in bytes

NO_PARAMS = 10
PARAMS_HEADER_SIZE = 3  # Number of 32-bit words in header of params block
PARAMS_BASE_SIZE = 4 * (PARAMS_HEADER_SIZE + NO_PARAMS)
BLOCK_INDEX_HEADER_WORDS = 3
BLOCK_INDEX_ROW_WORDS = 2

RECORD_SPIKE_BIT = 1 << 0
RECORD_STATE_BIT = 1 << 1
RECORD_GSYN_BIT = 1 << 2
RECORDING_ENTRY_BYTE_SIZE = 4
BITS_PER_WORD = 32.0

# From neuron common-typedefs.h
SYNAPSE_INDEX_BITS = 8
MAX_NEURON_SIZE = (1 << SYNAPSE_INDEX_BITS)
OUT_SPIKE_SIZE = (MAX_NEURON_SIZE >> 5)  # The size of each output spike line
OUT_SPIKE_BYTES = OUT_SPIKE_SIZE * 4  # The number of bytes for each spike line
V_BUFFER_SIZE_PER_TICK_PER_NEURON = 4
GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON = 4

INFINITE_SIMULATION = 4294967295

#from synaptic manager
SYNAPTIC_ROW_HEADER_WORDS = 2 + 1   # Words - 2 for row lenth and number of
                                        #  rows and 1 for plastic region size
                                        # (which might be 0)

ROW_LEN_TABLE_ENTRIES = [0, 1, 8, 16, 32, 64, 128, 256]
ROW_LEN_TABLE_SIZE = 4 * len(ROW_LEN_TABLE_ENTRIES)

X_CHIPS = 8
Y_CHIPS = 8
CORES_PER_CHIP = 18
MASTER_POPULATION_ENTRIES = (X_CHIPS * Y_CHIPS * CORES_PER_CHIP)
MASTER_POPULATION_TABLE_SIZE = 2 * MASTER_POPULATION_ENTRIES  # 2 bytes per
                                                              # entry
NA_TO_PA_SCALE = 1000.0
SDRAM_BASE_ADDR = 0x70000000
####might not be used
WEIGHT_FLOAT_TO_FIXED_SCALE = 16.0
SCALE = WEIGHT_FLOAT_TO_FIXED_SCALE * NA_TO_PA_SCALE
####

#natively supported delays for all models
MAX_SUPPORTED_DELAY_TICS = 16
MAX_DELAY_BLOCKS = 8
MAX_TIMER_TICS_SUPPORTED_PER_BLOCK = 16

#debug filter positions
#multicast packets which are sent from a local chip where the local router has
# router entry for it (this is default routed to the monitor core which
#currently drops the packet).
MON_CORE_DEFAULT_RTD_PACKETS_FILTER_POSITION = 12

#Model Names
APP_MONITOR_CORE_APPLICATION_ID = 0xAC0
IF_CURRENT_EXP_CORE_APPLICATION_ID = 0xAC1
SPIKESOURCEARRAY_CORE_APPLICATION_ID = 0xAC2
SPIKESOURCEPOISSON_CORE_APPLICATION_ID = 0xAC3
DELAY_EXTENSION_CORE_APPLICATION_ID = 0xAC4
MUNICH_MOTOR_CONTROL_CORE_APPLICATION_ID = 0xAC5
COMMAND_SENDER_CORE_APPLICATION_ID = 0xAC6
IF_CONDUCTIVE_EXP_CORE_APPLICATION_ID = 0xAC7
IZK_CURRENT_EXP_CORE_APPLICATION_ID = 0xAC8
SPIKE_INJECTOR_CORE_APPLICATION_ID = 0xAC9

EDGES = Enum(
    value="EDGES",
    names=[("EAST", 0),
           ("NORTH_EAST", 1),
           ("NORTH", 2),
           ("WEST", 3),
           ("SOUTH_WEST", 4),
           ("SOUTH", 5)])


POPULATION_BASED_REGIONS = Enum(
    value="POPULATION_BASED_REGIONS",
    names=[('SYSTEM', 0),
           ('NEURON_PARAMS', 1),
           ('SYNAPSE_PARAMS', 2),
           ('ROW_LEN_TRANSLATION', 3),
           ('MASTER_POP_TABLE', 4),
           ('SYNAPTIC_MATRIX', 5),
           ('STDP_PARAMS', 6),
           ('SPIKE_HISTORY', 7),
           ('POTENTIAL_HISTORY', 8),
           ('GSYN_HISTORY', 9)])
