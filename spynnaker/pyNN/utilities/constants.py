# Copyright (c) 2014 The University of Manchester
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


import math
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_KB)

POSSION_SIGMA_SUMMATION_LIMIT = 3.0

BLOCK_INDEX_HEADER_WORDS = 3
BLOCK_INDEX_ROW_WORDS = 2

RECORD_SPIKE_BIT = 1 << 0
RECORD_STATE_BIT = 1 << 1
RECORD_GSYN_BIT = 1 << 2
RECORDING_ENTRY_BYTE_SIZE = BYTES_PER_WORD


# From neuron common-typedefs.h
SYNAPSE_INDEX_BITS = 8
MAX_NEURON_SIZE = 1 << SYNAPSE_INDEX_BITS
#: The size of each output spike line
OUT_SPIKE_SIZE = MAX_NEURON_SIZE >> 5
#: The number of bytes for each spike line
OUT_SPIKE_BYTES = OUT_SPIKE_SIZE * BYTES_PER_WORD
V_BUFFER_SIZE_PER_TICK_PER_NEURON = BYTES_PER_WORD
GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON = 2 * BYTES_PER_WORD

SPIKE_BUFFER_SIZE_BUFFERING_IN = 1 * 1024 * BYTES_PER_KB
EIEIO_SPIKE_BUFFER_SIZE_BUFFERING_OUT = 1 * 1024 * BYTES_PER_KB
EIEIO_BUFFER_SIZE_BEFORE_RECEIVE = 512 * BYTES_PER_KB

INFINITE_SIMULATION = 4294967295

# from synaptic manager
#: Words: 2 for row length and number of rows and 1 for plastic region size
#: (which might be 0)
SYNAPTIC_ROW_HEADER_WORDS = 2 + 1

NA_TO_PA_SCALE = 1000.0

# might not be used
WEIGHT_FLOAT_TO_FIXED_SCALE = 16.0
SCALE = WEIGHT_FLOAT_TO_FIXED_SCALE * NA_TO_PA_SCALE

#: natively supported delays for all abstract_models
MAX_SUPPORTED_DELAY_TICS = 64
MAX_DELAY_BLOCKS = 64
DELAY_MASK = (1 << int(math.log2(MAX_SUPPORTED_DELAY_TICS))) - 1
MAX_TIMER_TICS_SUPPORTED_PER_BLOCK = 16

#: the minimum supported delay slot between two neurons
MIN_SUPPORTED_DELAY = 1

#: The partition ID used for spike data
SPIKE_PARTITION_ID = "SPIKE"

# names for recording components
SPIKES = 'spikes'
MEMBRANE_POTENTIAL = "v"
GSYN_EXCIT = "gsyn_exc"
GSYN_INHIB = "gsyn_inh"
REWIRING = "rewiring"

#: The partition ID used for Poisson live control data
LIVE_POISSON_CONTROL_PARTITION_ID = "CONTROL"

#: The maximum row length of the master population table
POP_TABLE_MAX_ROW_LENGTH = 256

#: The name of the partition for Synaptic SDRAM
SYNAPSE_SDRAM_PARTITION_ID = "SDRAM Synaptic Inputs"

#: The conservative amount of write bandwidth available on a chip
WRITE_BANDWIDTH_BYTES_PER_SECOND = 250 * 1024 * 1024
