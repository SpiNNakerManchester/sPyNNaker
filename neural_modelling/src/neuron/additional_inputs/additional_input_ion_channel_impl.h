/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _ADDITIONAL_INPUT_ION_CHANNEL_H_
#define _ADDITIONAL_INPUT_ION_CHANNEL_H_

#include "additional_input.h"

//----------------------------------------------------------------------------
// Model from Liu, Y. H., & Wang, X. J. (2001). Spike-frequency adaptation of
// a generalized leaky integrate-and-fire model neuron. Journal of
// Computational Neuroscience, 10(1), 25-45. doi:10.1023/A:1008916026143
//----------------------------------------------------------------------------

typedef struct additional_input_t {
    // n = probability of gate being open
    REAL    n;
    // gK
    REAL 	gK;
    // current
    REAL	I_k;
    // Ek
    REAL	Ek;

} additional_input_t;

static input_t additional_input_get_input_value_as_current(
        additional_input_pointer_t additional_input,
        state_t membrane_voltage) {
	use(membrane_voltage);


//	update alpha_n and beta_n values for this membrane voltage
	REAL alpha_n = (0.01*(membrane_voltage+55)) / (1 - expk(-0.1*(membrane_voltage+55)));
	REAL beta_n = 0.125*expk(-0.0125*(membrane_voltage+65));

	// update tau_n and n_inf values
	REAL tau_n = 1 / (alpha_n + beta_n);
	REAL n_inf = (alpha_n) / (alpha_n + beta_n);

	// update n value - change the 0.1 to ts at some point
	additional_input->n = n_inf + (additional_input->n - n_inf)*expk(-0.1/tau_n);

//	io_printf(IO_BUF, "n=%k\n", additional_input->n);


	// n^4 and use this to update the current through the channel
	REAL n_pow = additional_input->n * additional_input->n * additional_input->n * additional_input->n;

	// update current according to equation I_k = gK*n**4*(V-Ek)
	additional_input->I_k = additional_input->gK * n_pow * (membrane_voltage - additional_input->Ek);
//	io_printf(IO_BUF, "current=%k\n", additional_input->I_k);


	// return the current
	return additional_input->I_k;
}

static void additional_input_has_spiked(
        additional_input_pointer_t additional_input) {
    // do nothing
    additional_input->n = additional_input->n;
}

#endif // _ADDITIONAL_INPUT_ION_CHANNEL_H_
