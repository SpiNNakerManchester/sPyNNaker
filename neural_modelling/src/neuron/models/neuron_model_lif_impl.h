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
//! \brief Leaky Integrate and Fire neuron type
#ifndef _NEURON_MODEL_LIF_CURR_IMPL_H_
#define _NEURON_MODEL_LIF_CURR_IMPL_H_

#include "neuron_model.h"

/////////////////////////////////////////////////////////////
//! definition for LIF neuron parameters
typedef struct neuron_t {
    //! membrane voltage [mV]
    REAL     V_membrane;

    //! membrane resting voltage [mV]
    REAL     V_rest;

    //! membrane resistance [MOhm]
    REAL     R_membrane;

    //! 'fixed' computation parameter - time constant multiplier for
    //! closed-form solution
    //! exp(-(machine time step in ms)/(R * C)) [.]
    REAL     exp_TC;

    //! offset current [nA]
    REAL     I_offset;

    //! countdown to end of next refractory period [timesteps]
    int32_t  refract_timer;

    //! post-spike reset membrane voltage [mV]
    REAL     V_reset;

    //! refractory time of neuron [timesteps]
    int32_t  T_refract;
} neuron_t;

//! LIF global parameters
typedef struct global_neuron_params_t {
} global_neuron_params_t;

//! \brief simple Leaky I&F ODE
//! \param[in,out] neuron: The neuron to update
//! \param[in] V_prev: previous voltage
//! \param[in] input_this_timestep: The input to apply
static inline void lif_neuron_closed_form(
        neuron_t *neuron, REAL V_prev, input_t input_this_timestep) {
    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // update membrane voltage
    neuron->V_membrane = alpha - (neuron->exp_TC * (alpha - V_prev));
}

static state_t neuron_model_state_update(
        uint16_t num_excitatory_inputs, const input_t *exc_input,
        uint16_t num_inhibitory_inputs, const input_t *inh_input,
        input_t external_bias, REAL current_offset, neuron_t *restrict neuron) {

    // If outside of the refractory period
    if (neuron->refract_timer <= 0) {
        REAL total_exc = 0;
        REAL total_inh = 0;

        for (int i=0; i < num_excitatory_inputs; i++) {
            total_exc += exc_input[i];
        }
        for (int i=0; i< num_inhibitory_inputs; i++) {
            total_inh += inh_input[i];
        }
        // Get the input in nA
        input_t input_this_timestep =
                total_exc - total_inh + external_bias + neuron->I_offset + current_offset;

        lif_neuron_closed_form(
                neuron, neuron->V_membrane, input_this_timestep);
    } else {
        // countdown refractory timer
        neuron->refract_timer--;
    }
    return neuron->V_membrane;
}

static void neuron_model_has_spiked(neuron_t *restrict neuron) {
    // reset membrane voltage
    neuron->V_membrane = neuron->V_reset;

    // reset refractory timer
    neuron->refract_timer  = neuron->T_refract;
}

static state_t neuron_model_get_membrane_voltage(const neuron_t *neuron) {
    return neuron->V_membrane;
}

#endif // _NEURON_MODEL_LIF_CURR_IMPL_H_
