#ifndef __DELAY_EXTENSION_H__
#define __DELAY_EXTENSION_H__

#include <common-typedefs.h>

// Constants
#define DELAY_STAGE_LENGTH  16

//! region identifiers
enum region_identifiers {
    SYSTEM = 0,
    DELAY_PARAMS = 1,
    PROVENANCE_REGION = 2,
    EXPANDER_REGION = 3
};

struct delay_parameters_t {
    uint32_t key;
    uint32_t incoming_key;
    uint32_t incoming_mask;
    uint32_t n_atoms;
    uint32_t n_delay_stages;
    uint32_t random_backoff;
    uint32_t time_beween_spikes;
    uint32_t n_outgoing_edges; // unused
    uint32_t delay_blocks[];
};

#define pack_delay_index_stage(index, stage) \
    ((index & 0xFF) | ((stage & 0xFF) << 8))
#define unpack_delay_index(packed) (packed & 0xFF)
#define unpack_delay_stage(packed) ((packed >> 8) & 0xFF)

#endif // __DELAY_EXTENSION_H__
