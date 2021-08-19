#ifndef _MY_WEIGHT_H_
#define _MY_WEIGHT_H_

// Because spin1_memcpy() is used in various places
#include <spin1_api.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>
#include <neuron/synapse_row.h>

#include <debug.h>

// A structure for the variables
typedef struct {
    int32_t min_weight;
    int32_t max_weight;

    int32_t my_parameter;

    // TODO: Put in all required parameters

} plasticity_weight_region_data_t;

// An intermediate data structure; can have more accuracy and use more storage
// than the variable structure e.g. weight might be 16-bit but stored as 32-bit
// here
typedef struct {
    int32_t initial_weight;

    int32_t potentiation;
    int32_t depression;

    const plasticity_weight_region_data_t *weight_region;

    // TODO: Put in any variables required in the intermediate state
} weight_state_t;

// TODO: Ensure this includes and implements the correct interface
#include <neuron/plasticity/stdp/weight_dependence/weight_one_term.h>

// The external variables of the weight rule
extern plasticity_weight_region_data_t *plasticity_weight_region_data;

//---------------------------------------
// STDP weight dependence functions
//---------------------------------------
static inline weight_state_t weight_get_initial(
        weight_t weight, index_t synapse_type) {

    // TODO: Store the data in the intermediate data structure
    return (weight_state_t ) {
        .initial_weight = (int32_t) weight,
        .potentiation = 0,
        .depression = 0,
        .weight_region = &plasticity_weight_region_data[synapse_type]
    };
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t depression) {

    // TODO: Perform intermediate operations in relation to depression
    // Note: Can save up to perform complex operations until the end
    state.depression += depression;
    return state;
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t potentiation) {

    // TODO: Perform intermediate operations in relation to potentiation
    // Note: Can save up to perform complex operations until the end
    state.potentiation += potentiation;
    return state;
}

//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state) {

    // TODO: Perform operations to get the final weight from the intermediate
    // state, taking into account all potentiation and depression
    // Note: it is recommended to do a single complex operation here rather
    // than one for each potentiation or depression if possible

    int32_t potentiation =
            new_state.potentiation * new_state.weight_region->my_parameter;
    int32_t depression =
            new_state.depression * new_state.weight_region->my_parameter;

    int32_t new_weight = new_state.initial_weight + potentiation - depression;

    // Clamp new weight
    new_weight = MIN(
            new_state.weight_region->max_weight,
            MAX(new_weight, new_state.weight_region->min_weight));

    log_debug("old_weight:%u, potentiation:%d, depression:%d, "
            "scaled potentiation:%d, scaled depression:%d, new_weight:%d",
            new_state.initial_weight, new_state.potentiation,
            new_state.depression, potentiation, depression, new_weight);

    return (weight_t) new_weight;
}

#endif // _MY_WEIGHT_H_
