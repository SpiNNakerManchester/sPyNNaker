#ifndef _WEIGHT_ERBP_IMPL_H_
#define _WEIGHT_ERBP_IMPL_H_

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

    uint32_t weight_shift;
    uint32_t syn_type;

    REAL reg_rate;

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
extern plasticity_weight_region_data_t *plasticity_weight_region_data;
extern uint32_t *weight_multiply_right_shift;

//---------------------------------------
// STDP weight dependance functions
//---------------------------------------
static inline weight_state_t weight_get_initial(weight_t weight,
                                                index_t synapse_type) {

    return (weight_state_t ) {
        .initial_weight = (int32_t) weight,
        .a2_plus = 0,
        .a2_minus = 0,
        .weight_region = &plasticity_weight_region_data[synapse_type],
    };
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_depression(
        weight_state_t state, int32_t a2_minus) {
    state.a2_minus += a2_minus;
    return state;
}

//---------------------------------------
static inline weight_state_t weight_one_term_apply_potentiation(
        weight_state_t state, int32_t a2_plus) {
    state.a2_plus += a2_plus;
    return state;
}

//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state, REAL diff_to_target) {

    // Scale potentiation and depression
    // **NOTE** A2+ and A2- are pre-scaled into weight format
    int32_t scaled_a2_plus = // new_state.a2_plus; // << 1;
    		maths_fixed_mul16(new_state.a2_plus, new_state.weight_region->a2_plus, 15);
//    		STDP_FIXED_MUL_16X16(
//        new_state.a2_plus, new_state.weight_region->a2_plus);
    int32_t scaled_a2_minus = // new_state.a2_minus; // << 1;
    		maths_fixed_mul16(new_state.a2_minus, new_state.weight_region->a2_minus, 15);
//    		STDP_FIXED_MUL_16X16(
//        new_state.a2_minus, new_state.weight_region->a2_minus);

    // Apply all terms to initial weight
    int32_t new_weight = new_state.initial_weight + scaled_a2_plus
                         - scaled_a2_minus;

    uint32_t type = new_state.weight_region->syn_type;
//    io_printf(IO_BUF, "Diff to tar:%k \n", diff_to_target);
    // do rate based regularisation

//    REAL up_fact = diff_to_target * 0.1; // normalised by rate (1/10hz)
    if (new_state.weight_region->reg_rate > 0.0k){
				if (diff_to_target > 0.1k) {
//		io_printf(IO_BUF, "Reg up \n");
					if (type == 0) {
//			new_weight = new_weight * (1.0k);
						new_weight = new_weight
								+ (new_weight * diff_to_target * new_state.weight_region->reg_rate);
					} else if (type == 2) {
						new_weight = new_weight
								- (new_weight * diff_to_target * new_state.weight_region->reg_rate);
//			new_weight = new_weight * 0.9k;
					}

				} else if (diff_to_target < 0.1k) {
//		io_printf(IO_BUF, "Reg down \n");
					if (type == 0) {
//			new_weight = new_weight * 0.9k;
						new_weight = new_weight
								+ (new_weight * diff_to_target * new_state.weight_region->reg_rate);
					} else if (type == 2) {
						new_weight = new_weight
								- (new_weight * diff_to_target * new_state.weight_region->reg_rate);
//			new_weight = new_weight * (1.0k);
					}
				}

    }

    // Clamp new weight
    new_weight = MIN(new_state.weight_region->max_weight,
                     MAX(new_weight, new_state.weight_region->min_weight));

    if (print_plasticity) {
    	io_printf(IO_BUF, "            old_weight:%u, a2+:%d, a2-:%d, scaled a2+:%d, scaled a2-:%d,"
              " new_weight:%d\n",
              new_state.initial_weight, new_state.a2_plus, new_state.a2_minus,
              scaled_a2_plus, scaled_a2_minus, new_weight);
    }

    return (weight_t) new_weight;
}


//static inline weight_t weight_regularisation(weight_state_t new_state,
//		REAL diff_to_target) {
//
//	int32_t new_weight;
//
//
//
//    // Clamp new weight
//    new_weight = MIN(new_state.weight_region->max_weight,
//                     MAX(new_weight, new_state.weight_region->min_weight));
//
//
//
//    return (weight_t) new_weight;
//
//}


#endif // _WEIGHT_ERBP_IMPL_H_
