#ifndef _SYNAPSE_STRUCUTRE_WEIGHT_IMPL_H_
#define _SYNAPSE_STRUCUTRE_WEIGHT_IMPL_H_

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse types have weights and eligibility traces
typedef int32_t plastic_synapse_t;

// The update state is purely a weight state
typedef weight_state_t update_state_t;

// The final state is just a weight as this is
// Both the weight and the synaptic word
typedef weight_t final_state_t;

//---------------------------------------
// Synapse interface functions
//---------------------------------------
// Synapse parameter get and set helpers
static inline int32_t synapse_structure_get_weight(plastic_synapse_t state) {
    return (state >> 16);
}

static inline int32_t synapse_structure_get_eligibility_trace(plastic_synapse_t state) {
    return (state & 0xFFFF);
}

static inline int32_t synapse_structure_update_state(int32_t trace, int32_t weight) {
    return (plastic_synapse_t)(weight << 16 | trace);
}

static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {
    return weight_get_initial(synapse_structure_get_weight(synaptic_word), synapse_type);
}

//---------------------------------------
static inline final_state_t synapse_structure_get_final_state(
        update_state_t state) {
    return weight_get_final(state);
}

//---------------------------------------
static inline weight_t synapse_structure_get_final_weight(
        final_state_t final_state) {
    return final_state;
}

/*
//---------------------------------------
static inline plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state) {
    return final_state;
}
*/

#endif  // _SYNAPSE_STRUCUTRE_WEIGHT_IMPL_H_
