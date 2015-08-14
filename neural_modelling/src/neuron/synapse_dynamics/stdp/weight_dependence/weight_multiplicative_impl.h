#ifndef _WEIGHT_MULTIPLICATIVE_IMPL_H_
#define _WEIGHT_MULTIPLICATIVE_IMPL_H_

// Include generic plasticity maths functions
#include "../common/maths.h"
#include "../common/stdp_typedefs.h"
#include "../../../synapse_row.h"

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

    uint32_t weight_multiply_right_shift;
    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t
    plasticity_weight_region_data[SYNAPSE_TYPE_COUNT];
extern uint32_t weight_multiply_right_shift[SYNAPSE_TYPE_COUNT];

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
        weight_state_t state, int32_t depression) {

    // Calculate scale
    // **NOTE** this calculation must be done at runtime-defined weight
    // fixed-point format
    int32_t scale = maths_fixed_mul16(
        state.weight - state.weight_region->min_weight,
        state.weight_region->a2_minus, state.weight_multiply_right_shift);

    // Multiply scale by depression and subtract
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight -= STDP_FIXED_MUL_16X16(scale, depression);
    return state;
}
//---------------------------------------
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t potentiation) {
    // Calculate scale
    // **NOTE** this calculation must be done at runtime-defined weight
    // fixed-point format
    int32_t scale = maths_fixed_mul16(
        state.weight_region->max_weight - state.weight,
        state.weight_region->a2_plus, state.weight_multiply_right_shift);

    // Multiply scale by potentiation and add
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight += STDP_FIXED_MUL_16X16(scale, potentiation);
    return state;
}
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state) {
    log_debug("\tnew_weight:%d\n", new_state.weight);

    return (weight_t) new_state.weight;
}

#endif  // _WEIGHT_MULTIPLICATIVE_IMPL_H_
