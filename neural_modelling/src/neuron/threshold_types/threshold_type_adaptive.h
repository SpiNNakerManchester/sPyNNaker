#ifndef _THRESHOLD_TYPE_ADAPTIVE_H_
#define _THRESHOLD_TYPE_ADAPTIVE_H_

#include "threshold_type.h"
#include <neuron/decay.h>
#include "debug.h"

typedef struct threshold_type_t {

    // The value of the static threshold
    REAL B; // Capital B(t)
    REAL b; // b(t)
    REAL b_0; // small b^0
    decay_t e_to_dt_on_tau_a; // rho
    REAL beta;
    REAL adpt; // beta/tau_a
    REAL z; // has spiked at time=t
} threshold_type_t;


static void _print_threshold_params(threshold_type_pointer_t threshold_type){
	log_info("B: %k, "
			"b: %k, "
			"b_0: %k, "
			"e_to_dt_on_tau_a: %u, "
			"beta: %k, "
			"adpt: %k, "
			"z: %k",
			threshold_type->B,
			threshold_type->b,
			threshold_type->b_0,
			threshold_type->e_to_dt_on_tau_a,
			threshold_type->beta,
			threshold_type->adpt,
			threshold_type->z);
}


static inline bool threshold_type_is_above_threshold(state_t value,
                        threshold_type_pointer_t threshold_type) {

	_print_threshold_params(threshold_type);

	// test for exceeding threshold at previous timestep
	bool crossed_at_previous = REAL_COMPARE(value, >=, threshold_type->B);

	// calculate z from previous timestep
	if (crossed_at_previous){
		// Set z=1 for use on next timestep
		threshold_type->z=1;
	}

	// Evolve threshold dynamics (decay to baseline)
	// Update small b (same regardless of spike - uses z from previous timestep)
	threshold_type->b =
			decay_s1615(threshold_type->b, threshold_type->e_to_dt_on_tau_a)
			+ (1k - decay_s1615(1k,threshold_type->e_to_dt_on_tau_a)) * 1000 * threshold_type->z;
//			+ (threshold_type->adpt) * threshold_type->z;

	// Update large B
	threshold_type->B = threshold_type->b_0 + threshold_type->beta*threshold_type->b;

    return crossed_at_previous;
}

#endif // _THRESHOLD_TYPE_ADAPTIVE_H_
