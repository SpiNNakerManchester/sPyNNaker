#ifndef SYNAPSE_STRUCUTRE_WEIGHT_AND_TRACE_IMPL_H
#define SYNAPSE_STRUCUTRE_WEIGHT_AND_TRACE_IMPL_H

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse contains normal 16-bit weight, a small state machine and an
// accumulator
typedef struct plastic_synapse_t {
    weight_t weight;

    uint16_t trace;
} plastic_synapse_t;

//// The update state is a weight state with 32-bit ARM-friendly versions of the
//// accumulator and the state
typedef struct update_state_t {
    weight_state_t weight_state;

    int16_t trace;
    uint32_t type;
} update_state_t;

typedef plastic_synapse_t final_state_t;

#include "synapse_structure.h"

static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {

    // Create update state, using weight dependance to initialise the weight
    // state And copying other parameters from the synaptic word into 32-bit
    // form
    update_state_t update_state;
    update_state.weight_state = weight_get_initial(synaptic_word.weight,
                                                   synapse_type);
    update_state.trace = synaptic_word.trace;
    update_state.type = synapse_type;
    return update_state;
}

//---------------------------------------
static inline final_state_t synapse_structure_get_final_state(
        update_state_t state, REAL diff_to_target) {

    // Get weight from state
    weight_t weight = weight_get_final(state.weight_state, diff_to_target);

    final_state_t final;
    final.weight = weight;
    final.trace = state.trace;

    // Build this into synaptic word along with updated accumulator and state
    return final;
}

//---------------------------------------
static inline weight_t synapse_structure_get_final_weight(
        final_state_t final_state) {
    return final_state.weight;
}

//---------------------------------------
static inline plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state) {
    return final_state;
}

#endif // SYNAPSE_STRUCUTRE_WEIGHT_AND_TRACE_IMPL_H
