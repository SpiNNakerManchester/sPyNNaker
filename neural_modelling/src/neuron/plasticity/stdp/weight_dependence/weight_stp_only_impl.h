#ifndef _WEIGHT_ADDITIVE_ONE_TERM_IMPL_H_
#define _WEIGHT_ADDITIVE_ONE_TERM_IMPL_H_

// Include generic plasticity maths functions
#include "../../common/maths.h"
#include "../../common/stdp_typedefs.h"
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
    int32_t initial_weight;

    int32_t a2_plus;
    int32_t a2_minus;

    const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

#include "weight_one_term.h"

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t
    plasticity_weight_region_data[SYNAPSE_TYPE_COUNT];

//---------------------------------------
// STDP weight dependance functions
//---------------------------------------
static inline weight_state_t weight_get_initial(weight_t weight,
                                                index_t synapse_type) {

    return (weight_state_t ) {
        .initial_weight = (int32_t) weight,
        .a2_plus = 0,
        .a2_minus = 0,
        .weight_region = &plasticity_weight_region_data[synapse_type]
    };
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t a2_minus) {
	use(a2_minus);
    return state;
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus) {
	use(a2_plus);
    return state;
}

//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state) {

    return (weight_t) new_state.initial_weight;
}

#endif // _WEIGHT_ADDITIVE_ONE_TERM_IMPL_H_
