#ifndef _WEIGHT_MULTIPLICATIVE_IMPL_H_
#define _WEIGHT_MULTIPLICATIVE_IMPL_H_

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>
#include <neuron/synapse_row.h>

#include <debug.h>

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
    int32_t min_weight;
    int32_t max_weight;

    int32_t a2_plus;
    int32_t a2_minus;
} plasticity_weight_region_data_t;

typedef struct {
    int32_t weight;

    int32_t a2_plus;
    int32_t a2_minus;

    uint32_t weight_multiply_right_shift;
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t *plasticity_weight_region_data;
extern uint32_t *weight_multiply_right_shift;

//---------------------------------------
// Weight dependance functions
//---------------------------------------
static inline weight_state_t weight_get_initial(weight_t weight,
        index_t synapse_type) {
    return (weight_state_t ) {
        .weight = (int32_t) weight,
        .weight_multiply_right_shift =
            weight_multiply_right_shift[synapse_type],
        .weight_region = &plasticity_weight_region_data[synapse_type]
    };
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t depression_multiplier) {

	io_printf(IO_BUF, "\n            Do Depression\n");
	io_printf(IO_BUF, "                  Weight prior to depression: %u\n",state.weight);

    // Calculate scale
    // **NOTE** this calculation must be done at runtime-defined weight
    // fixed-point format
//    int32_t scale = maths_fixed_mul16(
//        state.weight - state.weight_region->min_weight,
////        state.weight_region->a2_minus,
//		depression_multiplier,
//		state.weight_multiply_right_shift);

    // Multiply scale by depression and subtract
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight -= STDP_FIXED_MUL_16X16(state.weight, depression_multiplier);

    io_printf(IO_BUF, "                  Weight after depression: %u\n\n",state.weight);

    return state;
}
//---------------------------------------
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t potentiation) {

	// add fixed amount
    state.a2_plus += state.weight_region->a2_plus;

    return state;

}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state) {
    log_debug("\tnew_weight:%d\n", new_state.weight);

    // first do Depression (as this would have happened first)


//    // Now do potentiation (check against lower limit)
//    int32_t scaled_a2_plus = STDP_FIXED_MUL_16X16(
//        new_state.a2_plus, new_state.weight_region->a2_plus);


    // Apply all terms to initial weight
    int32_t new_weight = new_state.weight + new_state.a2_plus;
                         // - scaled_a2_minus;

    io_printf(IO_BUF, "        old weight: %u, new weight: %u\n", new_state.weight,  new_weight);

    // Clamp new weight
    new_weight = MIN(new_state.weight_region->max_weight,
                      new_weight);

    new_state.weight = new_weight;

    return (weight_t) new_state.weight;
}

#endif  // _WEIGHT_MULTIPLICATIVE_IMPL_H_
