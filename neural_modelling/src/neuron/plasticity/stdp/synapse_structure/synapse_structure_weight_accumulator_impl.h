#ifndef _SYNAPSE_STRUCUTRE_WEIGHT_ACCUMULATOR_IMPL_H_
#define _SYNAPSE_STRUCUTRE_WEIGHT_ACCUMULATOR_IMPL_H_
#include <common-typedefs.h>

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse contains normal 16-bit weight and an accumulator
typedef struct plastic_synapse_t {
	// See python SynapseStructureWeightRecurrentAccumulator() for datastructure
    weight_t weight;
    int16_t pot_accumulator;
    int16_t dep_accumulator;
    uint16_t lock;
} plastic_synapse_t;

// The update state is a weight state with 32-bit ARM-friendly version of the
// accumulator
typedef struct update_state_t {
    weight_state_t weight_state;
    int32_t pot_accumulator;
    int32_t dep_accumulator;
    uint16_t lock;
	bool pre_waiting_post;
	uint32_t longest_post_pre_window_closing_time;
} update_state_t;

typedef plastic_synapse_t final_state_t;

#include "synapse_structure.h"

static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {

    // Create update state, using weight dependence to initialise the weight
    // state And copying other parameters from the synaptic word into 32-bit
    // form
    update_state_t update_state;

    //log_info("InSz: plastic_synapse_t %d, weight_state_t: %d, accumulator: %d\n", sizeof(synaptic_word),
    // sizeof(synaptic_word.weight), sizeof(synaptic_word.accumulator));
    //log_info("ss_get_update_state W: %d, A: %d\n", synaptic_word.weight, synaptic_word.accumulator);

    update_state.weight_state = weight_get_initial(synaptic_word.weight, synapse_type);
    update_state.pot_accumulator = (int32_t) synaptic_word.pot_accumulator;
    update_state.dep_accumulator = (int32_t) synaptic_word.dep_accumulator;
    update_state.lock = synaptic_word.lock;
	update_state.pre_waiting_post = true; // Set True, as this synapse has been fetched because the pre-synaptic neuron fired!
	update_state.longest_post_pre_window_closing_time = 0;
	/*
	log_info("ss_out W: %d, A: %d\n", update_state.weight_state, update_state.accumulator);
	log_info("OutSz: update_state %d, weight_state: %d, accumulator: %d,
				prewaitpost: %d, longwin: %d\n", sizeof(update_state), \
	  sizeof(update_state.weight_state), sizeof(update_state.accumulator),
		sizeof(update_state.pre_waiting_post), \
	  sizeof(update_state.longest_post_pre_window_closing_time));
	  */
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
        .pot_accumulator = (int16_t) state.pot_accumulator,
		.dep_accumulator = (int16_t ) state.dep_accumulator,
		.lock = state.lock
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

#endif //_SYNAPSE_STRUCUTRE_WEIGHT_ACCUMULATOR_IMPL_H_
