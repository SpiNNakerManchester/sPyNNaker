#ifndef _THRESHOLD_TYPE_STATIC_H_
#define _THRESHOLD_TYPE_STATIC_H_

#include "threshold_type.h"
#include <neuron/decay.h>

typedef struct threshold_type_t {

    // The value of the static threshold
    REAL threshold_value;
    REAL threshold_resting;
    decay_t threshold_decay;
    REAL threshold_adaptation;
} threshold_type_t;


void _print_threshold_params(threshold_type_pointer_t threshold_type){
	log_info("threshold_value: %k, "
			"threhsold_resting: %k, "
			"threshold_decay: %u, "
			"threshold_adaptation: %k",
			threshold_type->threshold_value,
			threshold_type->threshold_resting,
			threshold_type->threshold_decay,
			threshold_type->threshold_adaptation);
}


static inline bool threshold_type_is_above_threshold(state_t value,
                        threshold_type_pointer_t threshold_type) {

	_print_threshold_params(threshold_type);

	// Evolve threshold dynamics (decay to baseline)
	threshold_type->threshold_value =
			(threshold_type->threshold_value - threshold_type->threshold_resting)
			* threshold_type->threshold_decay + threshold_type->threshold_resting;

	// test for exceeding threshold
	bool spiked = REAL_COMPARE(value, >=, threshold_type->threshold_value);

	// if spiked adapt threshold
	if (spiked){
		threshold_type->threshold_value += threshold_type->threshold_adaptation;
	}

    return spiked;
}




#endif // _THRESHOLD_TYPE_STATIC_H_
