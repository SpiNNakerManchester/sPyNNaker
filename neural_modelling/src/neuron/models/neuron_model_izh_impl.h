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
//! \brief Izhekevich neuron type
#ifndef _NEURON_MODEL_IZH_CURR_IMPL_H_
#define _NEURON_MODEL_IZH_CURR_IMPL_H_

#include "neuron_model.h"

//! The state parameters of an Izhekevich model neuron
struct neuron_params_t {
    // nominally 'fixed' parameters
    REAL A;
    REAL B;
    REAL C;
    REAL D;

    // Variable-state parameters
    REAL V;
    REAL U;

    //! offset current [nA]
    REAL I_offset;

    //! current timestep in ms
    REAL time_step;

    //! next value of this_h (saved)
    REAL next_h;
};

//! The state variables of an Izhekevich model neuron
struct neuron_t {
    // nominally 'fixed' parameters
    REAL A;
    REAL B;
    REAL C;
    REAL D;

    // Variable-state parameters
    REAL V;
    REAL U;

    //! offset current [nA]
    REAL I_offset;

    //! current timestep
    REAL this_h;

    //! timestep to reset to when not just spiked
    REAL reset_h;
};

// Mark a value as possibly unused while not using any instructions, guaranteed
#ifndef __use
#define __use(x)    do { (void) (x); } while (0)
#endif

static inline void neuron_model_initialise(neuron_t *state, neuron_params_t *params,
		uint32_t n_steps_per_timestep) {
	state->A = params->A;
    state->B = params->B;
	state->C = params->C;
	state->D = params->D;
	state->V = params->V;
	state->U = params->U;
	state->I_offset = params->I_offset;
	state->this_h = params->next_h;
	state->reset_h = kdivui(params->time_step, n_steps_per_timestep);
}

static inline void neuron_model_save_state(neuron_t *state, neuron_params_t *params) {
	params->next_h = state->this_h;
	params->V = state->V;
	params->U = state->U;
}

/*! \brief For linear membrane voltages, 1.5 is the correct value. However
 * with actual membrane voltage behaviour and tested over an wide range of
 * use cases 1.85 gives slightly better spike timings.
 */
static const REAL SIMPLE_TQ_OFFSET = REAL_CONST(1.85);

/////////////////////////////////////////////////////////////
#if 0
// definition for Izhikevich neuron
static inline void neuron_ode(
        REAL t, REAL stateVar[], REAL dstateVar_dt[],
        neuron_t *neuron, REAL input_this_timestep) {
    REAL V_now = stateVar[1];
    REAL U_now = stateVar[2];
    log_debug(" sv1 %9.4k  V %9.4k --- sv2 %9.4k  U %9.4k\n", stateVar[1],
            neuron->V, stateVar[2], neuron->U);

    // Update V
    dstateVar_dt[1] =
            REAL_CONST(140.0)
            + (REAL_CONST(5.0) + REAL_CONST(0.0400) * V_now) * V_now - U_now
            + input_this_timestep;

    // Update U
    dstateVar_dt[2] = neuron->A * (neuron->B * V_now - U_now);
}
#endif

//! \brief The original model uses 0.04, but this (1 ULP larger?) gives better
//! numeric stability.
//!
//! Thanks to Mantas Mikaitis for this!
static const REAL MAGIC_MULTIPLIER = REAL_CONST(0.040008544921875);

/*!
 * \brief Midpoint is best balance between speed and accuracy so far.
 * \details From ODE solver comparison work, paper shows that Trapezoid version
 *      gives better accuracy at small speed cost
 * \param[in] h: threshold
 * \param[in,out] neuron: The model being updated
 * \param[in] input_this_timestep: the input
 */
static inline void rk2_kernel_midpoint(
        REAL h, neuron_t *neuron, REAL input_this_timestep) {
    // to match Mathematica names
    REAL lastV1 = neuron->V;
    REAL lastU1 = neuron->U;
    REAL a = neuron->A;
    REAL b = neuron->B;

    REAL pre_alph = REAL_CONST(140.0) + input_this_timestep - lastU1;
    REAL alpha = pre_alph
            + (REAL_CONST(5.0) + MAGIC_MULTIPLIER * lastV1) * lastV1;
    REAL eta = lastV1 + REAL_HALF(h * alpha);

    // could be represented as a long fract?
    REAL beta = REAL_HALF(h * (b * lastV1 - lastU1) * a);

    neuron->V += h * (pre_alph - beta
            + (REAL_CONST(5.0) + MAGIC_MULTIPLIER * eta) * eta);

    neuron->U += a * h * (-lastU1 - beta + b * eta);
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
        input_t external_bias, REAL current_offset, neuron_t *restrict neuron,
		REAL B_t) {
	__use(B_t);

    REAL total_exc = ZERO;
    REAL total_inh = ZERO;

    for (int i =0; i<num_excitatory_inputs; i++) {
        total_exc += exc_input[i];
    }
    for (int i =0; i<num_inhibitory_inputs; i++) {
        total_inh += inh_input[i];
    }

    input_t input_this_timestep = total_exc - total_inh
            + external_bias + neuron->I_offset + current_offset;

    // the best AR update so far
    rk2_kernel_midpoint(neuron->this_h, neuron, input_this_timestep);
    neuron->this_h = neuron->reset_h;

    return neuron->V;
}

//! \brief Indicates that the neuron has spiked
//! \param[in, out] neuron pointer to a neuron parameter struct which contains
//!     all the parameters for a specific neuron
static inline void neuron_model_has_spiked(neuron_t *restrict neuron) {
    // reset membrane voltage
    neuron->V = neuron->C;

    // offset 2nd state variable
    neuron->U += neuron->D;

    // simple threshold correction - next timestep (only) gets a bump
    neuron->this_h = neuron->reset_h * SIMPLE_TQ_OFFSET;
}

//! \brief get the neuron membrane voltage for a given neuron parameter set
//! \param[in] neuron: a pointer to a neuron parameter struct which contains
//!     all the parameters for a specific neuron
//! \return the membrane voltage for a given neuron with the neuron
//!     parameters specified in neuron
static inline state_t neuron_model_get_membrane_voltage(const neuron_t *neuron) {
    return neuron->V;
}

static inline void neuron_model_print_state_variables(const neuron_t *neuron) {
    log_debug("V = %11.4k ", neuron->V);
    log_debug("U = %11.4k ", neuron->U);
    log_debug("This h = %11.4k", neuron->this_h);
}

static inline void neuron_model_print_parameters(const neuron_t *neuron) {
    log_debug("A = %11.4k ", neuron->A);
    log_debug("B = %11.4k ", neuron->B);
    log_debug("C = %11.4k ", neuron->C);
    log_debug("D = %11.4k ", neuron->D);

    log_debug("I = %11.4k \n", neuron->I_offset);
    log_debug("Reset h = %11.4k", neuron->reset_h);
}

#endif   // _NEURON_MODEL_IZH_CURR_IMPL_H_
