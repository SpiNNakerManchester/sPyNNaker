#ifndef _SYNAPSE_STRUCTURE_WEIGHT_STEP_IMPL_H_
#define _SYNAPSE_STRUCTURE_WEIGHT_STEP_IMPL_H_

//---------------------------------------
// Structures
//---------------------------------------
// Plastic synapse types are just weights;
typedef weight_t plastic_synapse_t;

// The update state is purely a weight state
typedef weight_state_t update_state_t;

// The final state is just a weight as this is
// Both the weight and the synaptic word
typedef struct {
    weight_t weight;
    const plasticity_weight_region_data_t *weight_region;
} final_state_t;
//---------------------------------------
// Synapse interface functions
//---------------------------------------
static inline update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type) {
    return weight_get_initial(synaptic_word, synapse_type);
}

//---------------------------------------
static inline final_state_t synapse_structure_get_final_state(
        update_state_t state) {
    return (final_state_t) {
        .weight = weight_get_final(state),
        .weight_region = state.weight_region
    };
}

//---------------------------------------
// Apply a step function to calculated weight before adding it to buffer
//---------------------------------------
static inline weight_t synapse_structure_get_final_weight(
        final_state_t final_state) {
	// extract th_weight, min_weight, max_weight
	int32_t th_weight = final_state.weight_region->th_weight;
	int32_t min_weight = final_state.weight_region->min_weight;
	int32_t max_weight = final_state.weight_region->max_weight;
	// calculate final weight
	weight_t w = final_state.weight;
	if(w > th_weight){
		w = max_weight;
	}else
		w = min_weight;
	//log_info("after step function: %d", w);
    return w;
}

//---------------------------------------
static inline plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state) {
    return final_state.weight;
}

#endif  // _SYNAPSE_STRUCTURE_WEIGHT_STEP_IMPL_H_
