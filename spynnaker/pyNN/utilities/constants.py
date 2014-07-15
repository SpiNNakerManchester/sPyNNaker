"""
Utilities for accessing the location of memory regions on the board
"""
from spynnaker.pyNN.utilities import enums

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

#From spinnaker.h
SYSRAM_BASE = 0xe5000000
SYSRAM_SIZE = 0x00008000
SYSRAM_TOP = SYSRAM_BASE + SYSRAM_SIZE

#From sark.h
SV_SIZE = 0x1000
SYS_BOOT = 256
SYS_USER_BASE = (SYSRAM_BASE + SYS_BOOT)
SYS_USER_TOP = (SYSRAM_TOP - SV_SIZE)
SV_VCPU = SYS_USER_TOP  # Should be 0xe5007000

#Derived constants
SIZEOF_VCPU = 128

DEFAULT_MASK = 0xfffff800  # DEFAULT LOCATION FOR THE APP MASK

#Offsets of items in the vcpu structure
VCPU_OFFSETS = {"r": 0,  # uint r[8]; //!< 0 - r0-r7
                "psr": 32,  # uint psr; //!< 32 - cpsr
                "sp": 36,  # uint sp; //!< 36 - sp
                "lr": 40,  # uint lr; //!< 40 - lr
                "rt_code": 44,  # uchar rt_code; //!< 44 - RT error code
                "cpu_flags": 45,  # uchar cpu_flags;
                                  # //!< 45 - CPU flags (unused...)
                "cpu_state": 46,  # uchar cpu_state; //!< 46 - CPU state
                "app_id": 47,  # uchar app_id; //!< 47 - Application ID
                "mbox_ap_msg": 48,  # void *mbox_ap_msg;
                                    # //!< 48 - mbox msg MP->AP
                "mbox_mp_msg": 52,  # void *mbox_mp_msg;
                                    # //!< 52 - mbox msg AP->MP
                "mbox_ap_cmd": 54,  # volatile uchar mbox_ap_cmd;
                                    # //!< 56 - mbox command MP->AP
                "mbox_mp_cmd": 55,  # volatile uchar mbox_mp_cmd;
                                    # //!< 57 - mbox command AP->MP
                "sw_count": 56,  # ushort sw_count;
                                 # //!< 58 - SW error count (saturating)
                "sw_file": 60,  # char *sw_file;
                                # //!< 60 - SW source file name
                "sw_line": 64,  # uint sw_line;
                                # //!< 64 - SW source line (could be short?)
                "time": 68,  # uint time; //!< 68 - Time of loading
                "app_name": 72,  # char app_name[16]; //!< 72 - Application name
                "io_buf": 88,  # void *iobuf;
                               #  //!< 88 - IO buffer in SDRAM (or 0)
                "__PAD": 92,  # uint __PAD[5]; //!< 92 - (spare)
                "user0": 112,  # uint user0; //!< 112 - User word 0
                "user1": 116,  # uint user1; //!< 116 - User word 1
                "user2": 120,  # uint user2; //!< 120 - User word 2
                "user3": 124,  # uint user3; //!< 124 - User word 3
                }

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