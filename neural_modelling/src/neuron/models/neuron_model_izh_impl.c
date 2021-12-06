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

//! \file
//! \brief Izhekevich neuron implementation
#include "neuron_model_izh_impl.h"

#include <debug.h>

//! The global parameters of the Izhekevich neuron model
const global_neuron_params_t *global_params;

void neuron_model_set_global_neuron_params(
        const global_neuron_params_t *params) {
    global_params = params;
}

void neuron_model_print_state_variables(const neuron_t *neuron) {
    log_debug("V = %11.4k ", neuron->V);
    log_debug("U = %11.4k ", neuron->U);
}

void neuron_model_print_parameters(const neuron_t *neuron) {
    log_debug("A = %11.4k ", neuron->A);
    log_debug("B = %11.4k ", neuron->B);
    log_debug("C = %11.4k ", neuron->C);
    log_debug("D = %11.4k ", neuron->D);

    log_debug("I = %11.4k \n", neuron->I_offset);
}
