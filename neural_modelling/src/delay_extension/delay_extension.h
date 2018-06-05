#ifndef __DELAY_EXTENSION_H__
#define __DELAY_EXTENSION_H__

// Constants
#define DELAY_STAGE_LENGTH  16

//! region identifiers
typedef enum region_identifiers{
    SYSTEM = 0, DELAY_PARAMS = 1, PROVENANCE_REGION = 2, EXPANDER_REGION = 3
} region_identifiers;

enum parameter_positions {
    KEY, INCOMING_KEY, INCOMING_MASK, N_ATOMS, N_DELAY_STAGES,
    RANDOM_BACKOFF, TIME_BETWEEN_SPIKES, N_OUTGOING_EDGES, DELAY_BLOCKS
};

#define pack_delay_index_stage(index, stage) \
    ((index & 0xFF) | ((stage & 0xFF) << 8))
#define unpack_delay_index(packed) (packed & 0xFF)
#define unpack_delay_stage(packed) ((packed >> 8) & 0xFF)

#endif // __DELAY_EXTENSION_H__
