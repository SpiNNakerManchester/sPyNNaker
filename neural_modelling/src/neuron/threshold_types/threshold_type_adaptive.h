/*
 * Copyright (c) 2019 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef _THRESHOLD_TYPE_ADAPTIVE_H_
#define _THRESHOLD_TYPE_ADAPTIVE_H_

#include "threshold_type.h"
#include <neuron/decay.h>
#include "debug.h"

typedef struct threshold_type_t {

    REAL B; // Capital B(t)
    REAL b; // b(t)
    REAL b_0; // small b^0
    decay_t e_to_dt_on_tau_a; // rho
    REAL beta;
    decay_t adpt; // (1-rho)
    REAL scalar;

} threshold_type_t;

static REAL var_scal = 1;

static void _print_threshold_params(threshold_type_pointer_t threshold_type){
	io_printf(IO_BUF, "B: %k, "
			"b: %k, "
			"b_0: %k, "
			"e_to_dt_on_tau_a: %u, "
			"beta: %k, "
			"adpt: %u, \n"
			"scalar: %k, \n\n",
			threshold_type->B,
			threshold_type->b,
			threshold_type->b_0,
			threshold_type->e_to_dt_on_tau_a,
			threshold_type->beta,
			threshold_type->adpt,
			threshold_type->scalar
			);
}


static inline bool threshold_type_is_above_threshold(state_t value,
                        threshold_type_pointer_t threshold_type) {

	// Not used
	use(value);
	use(threshold_type);

    return false;
}

static inline void threshold_type_update_threshold(state_t z,
		threshold_type_pointer_t threshold_type){

//	_print_threshold_params(threshold_type);


	s1615 temp1 = decay_s1615(threshold_type->b, threshold_type->e_to_dt_on_tau_a);
	s1615 temp2 = decay_s1615(threshold_type->scalar, threshold_type->adpt) * z;

	threshold_type->b = temp1
			+ temp2;


//	// Evolve threshold dynamics (decay to baseline) and adapt if z=nonzero
//	// Update small b (same regardless of spike - uses z from previous timestep)
//	threshold_type->b =
//			decay_s1615(threshold_type->b, threshold_type->e_to_dt_on_tau_a)
//			+ decay_s1615(1000k, threshold_type->adpt) // fold scaling into decay to increase precision
//			* z; // stored on neuron
//
	// Update large B
	threshold_type->B = threshold_type->b_0 +
			threshold_type->beta*threshold_type->b;

}


#endif // _THRESHOLD_TYPE_ADAPTIVE_H_
