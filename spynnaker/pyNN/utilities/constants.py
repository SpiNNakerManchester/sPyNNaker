from enum import Enum

POSSION_SIGMA_SUMMATION_LIMIT = 3.0

BLOCK_INDEX_HEADER_WORDS = 3
BLOCK_INDEX_ROW_WORDS = 2

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
GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON = 8

SPIKE_BUFFER_SIZE_BUFFERING_IN = 1 * 1024 * 1024
EIEIO_SPIKE_BUFFER_SIZE_BUFFERING_OUT = 1 * 1024 * 1024
EIEIO_BUFFER_SIZE_BEFORE_RECEIVE = 512 * 1024

INFINITE_SIMULATION = 4294967295

# from synaptic manager
# Words - 2 for row length and number of rows and 1 for plastic region size
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

# the minimum supported delay slot between two neurons
MIN_SUPPORTED_DELAY = 1

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
           ('GSYN_HISTORY', 8),
           ('BUFFERING_OUT_STATE', 9),
           ('PROVENANCE_DATA', 10)])
