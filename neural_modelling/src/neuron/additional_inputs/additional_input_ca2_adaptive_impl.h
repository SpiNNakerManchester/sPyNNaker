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

#ifndef _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_
#define _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_

#include "additional_input.h"

//----------------------------------------------------------------------------
// Model from Liu, Y. H., & Wang, X. J. (2001). Spike-frequency adaptation of
// a generalized leaky integrate-and-fire model neuron. Journal of
// Computational Neuroscience, 10(1), 25-45. doi:10.1023/A:1008916026143
//----------------------------------------------------------------------------

typedef struct additional_input_t {
    // exp(-(machine time step in ms) / (TauCa))
    REAL    exp_TauCa;
    // Calcium current
    REAL    I_Ca2;
    // Influx of CA2 caused by each spike
    REAL    I_alpha;

} additional_input_t;

static input_t additional_input_get_input_value_as_current(
        additional_input_pointer_t additional_input,
        state_t membrane_voltage) {
	use(membrane_voltage);

    // Decay Ca2 trace
    additional_input->I_Ca2 *= additional_input->exp_TauCa;

    // Return the Ca2
    return -additional_input->I_Ca2;
}

static void additional_input_has_spiked(
        additional_input_pointer_t additional_input) {
    // Apply influx of calcium to trace
    additional_input->I_Ca2 += additional_input->I_alpha;
}

#endif // _ADDITIONAL_INPUT_CA2_ADAPTIVE_H_
