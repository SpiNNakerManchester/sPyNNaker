#ifndef _SYNAPSE_STRUCUTRE_WEIGHT_STATE_ACCUMULATOR_IMPL_H_
#define _SYNAPSE_STRUCUTRE_WEIGHT_STATE_ACCUMULATOR_IMPL_H_

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse contains normal 16-bit weight and an accumulator
typedef struct plastic_synapse_t {
    weight_t weight;

    int16_t accumulator;
} plastic_synapse_t;

// The update state is a weight state with 32-bit ARM-friendly version of the
// accumulator
typedef struct update_state_t {
    weight_state_t weight_state;

    int32_t accumulator;
} update_state_t;

typedef plastic_synapse_t final_state_t;

#include "neuron/plasticity/stdp/synapse_structure/synapse_structure.h"

static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {

    // Create update state, using weight dependance to initialise the weight
    // state And copying other parameters from the synaptic word into 32-bit
    // form
    update_state_t update_state;
    update_state.weight_state = weight_get_initial(synaptic_word.weight,
                                                   synapse_type);
    update_state.accumulator = (int32_t) synaptic_word.accumulator;
    return update_state;
}

//---------------------------------------
static inline final_state_t synapse_structure_get_final_state(
        update_state_t state) {

    // Get weight from state
    weight_t weight = weight_get_final(state.weight_state);

    // Build this into synaptic word along with updated accumulator and state
    return (final_state_t) {
        .weight = weight,
        .accumulator = (int16_t) state.accumulator
    };
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

#endif _SYNAPSE_STRUCUTRE_WEIGHT_STATE_ACCUMULATOR_IMPL_H_
