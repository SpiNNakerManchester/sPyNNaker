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

from enum import Enum
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

#: the minimum supported delay slot between two neurons
MIN_SUPPORTED_DELAY = 1


class POPULATION_BASED_REGIONS(Enum):
    """Regions for populations."""
    SYSTEM = 0
    NEURON_PARAMS = 1
    SYNAPSE_PARAMS = 2
    POPULATION_TABLE = 3
    SYNAPTIC_MATRIX = 4
    SYNAPSE_DYNAMICS = 5
    STRUCTURAL_DYNAMICS = 6
    NEURON_RECORDING = 7
    PROVENANCE_DATA = 8
    PROFILING = 9
    CONNECTOR_BUILDER = 10
    DIRECT_MATRIX = 11
    BIT_FIELD_FILTER = 12
    BIT_FIELD_BUILDER = 13
    BIT_FIELD_KEY_MAP = 14


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
