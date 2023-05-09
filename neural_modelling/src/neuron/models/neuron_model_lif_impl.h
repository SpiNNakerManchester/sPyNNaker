/*
 * Copyright (c) 2015 The University of Manchester
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

//! \file
//! \brief Leaky Integrate and Fire neuron type
#ifndef _NEURON_MODEL_LIF_CURR_IMPL_H_
#define _NEURON_MODEL_LIF_CURR_IMPL_H_

#include "neuron_model.h"

//! definition for LIF neuron parameters
struct neuron_params_t {
    //! membrane voltage [mV]
    REAL     V_init;

    //! membrane resting voltage [mV]
    REAL     V_rest;

    //! membrane capacitance [nF]
    REAL     c_m;

    //! membrane decay time constant
    REAL     tau_m;

    //! offset current [nA]
    REAL     I_offset;

    //! post-spike reset membrane voltage [mV]
    REAL     V_reset;

    //! refractory time of neuron [ms]
    REAL     T_refract_ms;

    //! initial refractory timer value (saved)
    int32_t  refract_timer_init;

    //! The time step in milliseconds
    REAL     time_step;
};


//! definition for LIF neuron state
struct neuron_t {
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
};

//! \brief Performs a ceil operation on an accum
//! \param[in] value The value to ceil
//! \return The ceil of the value
static inline int32_t lif_ceil_accum(REAL value) {
	int32_t bits = bitsk(value);
	int32_t integer = bits >> 15;
	int32_t fraction = bits & 0x7FFF;
	if (fraction > 0) {
	    return integer + 1;
	}
	return integer;
}

static inline void neuron_model_initialise(
		neuron_t *state, neuron_params_t *params, uint32_t n_steps_per_timestep) {
	REAL ts = kdivui(params->time_step, n_steps_per_timestep);
	state->V_membrane = params->V_init;
	state->V_rest = params->V_rest;
    state->R_membrane = kdivk(params->tau_m, params->c_m);
	state->exp_TC = expk(-kdivk(ts, params->tau_m));
	state->I_offset = params->I_offset;
    state->refract_timer = params->refract_timer_init;
	state->V_reset = params->V_reset;
	state->T_refract = lif_ceil_accum(kdivk(params->T_refract_ms, ts));
}

static inline void neuron_model_save_state(neuron_t *state, neuron_params_t *params) {
	params->V_init = state->V_membrane;
	params->refract_timer_init = state->refract_timer;
}

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

//! \brief primary function called in timer loop after synaptic updates
//! \param[in] num_excitatory_inputs: Number of excitatory receptor types.
//! \param[in] exc_input: Pointer to array of inputs per receptor type received
//!     this timer tick that produce a positive reaction within the neuron in
//!     terms of stimulation.
//! \param[in] num_inhibitory_inputs: Number of inhibitory receptor types.
//! \param[in] inh_input: Pointer to array of inputs per receptor type received
//!     this timer tick that produce a negative reaction within the neuron in
//!     terms of stimulation.
//! \param[in] external_bias: This is the intrinsic plasticity which could be
//!     used for ac, noisy input etc etc. (general purpose input)
//! \param[in,out] neuron: the pointer to a neuron parameter struct which
//!     contains all the parameters for a specific neuron
//! \return the value to be compared with a threshold value to determine if the
//!     neuron has spiked
static inline state_t neuron_model_state_update(
        uint16_t num_excitatory_inputs, const input_t *exc_input,
        uint16_t num_inhibitory_inputs, const input_t *inh_input,
        input_t external_bias, REAL current_offset, neuron_t *restrict neuron) {

    // If outside of the refractory period
    if (neuron->refract_timer <= 0) {
    	REAL total_exc = ZERO;
    	REAL total_inh = ZERO;

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

//! \brief Indicates that the neuron has spiked
//! \param[in, out] neuron pointer to a neuron parameter struct which contains
//!     all the parameters for a specific neuron
static inline void neuron_model_has_spiked(neuron_t *restrict neuron) {
    // reset membrane voltage
    neuron->V_membrane = neuron->V_reset;

    // reset refractory timer
    neuron->refract_timer  = neuron->T_refract;
}

//! \brief get the neuron membrane voltage for a given neuron parameter set
//! \param[in] neuron: a pointer to a neuron parameter struct which contains
//!     all the parameters for a specific neuron
//! \return the membrane voltage for a given neuron with the neuron
//!     parameters specified in neuron
static inline state_t neuron_model_get_membrane_voltage(const neuron_t *neuron) {
    return neuron->V_membrane;
}

static inline void neuron_model_print_state_variables(const neuron_t *neuron) {
	log_info("V membrane    = %11.4k mv", neuron->V_membrane);
	log_info("Refract timer = %u timesteps", neuron->refract_timer);
}

static inline void neuron_model_print_parameters(const neuron_t *neuron) {
    log_info("V reset       = %11.4k mv", neuron->V_reset);
    log_info("V rest        = %11.4k mv", neuron->V_rest);

    log_info("I offset      = %11.4k nA", neuron->I_offset);
    log_info("R membrane    = %11.4k Mohm", neuron->R_membrane);

    log_info("exp(-ms/(RC)) = %11.4k [.]", neuron->exp_TC);

    log_info("T refract     = %u timesteps", neuron->T_refract);
}


#endif // _NEURON_MODEL_LIF_CURR_IMPL_H_
