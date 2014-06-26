"""
COMMENT ME
"""

SDRAM_BASE_ADDR = 0x70000000
APP_START_ADDR = 0x404000

############
## All the the values below are deprecated.

# Load address of executable code
executable = int("404000", 16)
# Load address of synapses
synapses = int("70000000", 16)
# Load address of neuron data structures
neuron_base = int("74000000", 16)
neuron_offset = int("10000", 16)
# Load address of synapse lookup tables
lookup_base = int("74200000", 16)
lookup_offset = int("1000", 16)
# Load address of routing tables
route_base = int("74210000", 16)
# Load address of barrier words
barrier = int("74220000", 16)
# Storage address of diagnostic blocks
diag_base = int("74400000", 16)
diag_offset = int("40", 16)
# Storage address of firing rates
fr_base = int("74e00000", 16)
fr_offset = int("10000", 16)
# Storage address of membrane-potential traces
trace_base = int("75000000", 16)
trace_offset = int("100000", 16)
# Storage address of neuron spikes (or load address for spike source arrays)
spike_base = int("76000000", 16)
spike_offset = int("200000", 16)

sizeofshort = 2 # bytes
sizeofint = 4 # bytes
