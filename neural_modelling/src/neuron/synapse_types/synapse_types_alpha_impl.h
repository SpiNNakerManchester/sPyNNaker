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

/*!
 * \file
 * \brief implementation of synapse_types.h for an alpha synapse behaviour
 */

#ifndef _ALPHA_SYNAPSE_H_
#define _ALPHA_SYNAPSE_H_

//---------------------------------------
// Macros
//---------------------------------------
//! \brief Number of bits to encode the synapse type
//! \details <tt>ceil(log2(#SYNAPSE_TYPE_COUNT))</tt>
#define SYNAPSE_TYPE_BITS 1
//! \brief Number of synapse types
//! \details <tt>#NUM_EXCITATORY_RECEPTORS + #NUM_INHIBITORY_RECEPTORS</tt>
#define SYNAPSE_TYPE_COUNT 2

//! Number of excitatory receptors
#define NUM_EXCITATORY_RECEPTORS 1
//! Number of inhibitory receptors
#define NUM_INHIBITORY_RECEPTORS 1

#include <neuron/decay.h>
#include <debug.h>
#include "synapse_types.h"

//---------------------------------------
// Synapse parameters
//---------------------------------------
//! Parameters of an alpha synaptic input
typedef struct alpha_params_t {
	input_t lin_init;
	input_t exp_init;
	input_t q_init;
	REAL tau;
} alpha_params_t;

struct synapse_types_params_t {
	alpha_params_t exc;
	alpha_params_t inh;
	REAL time_step_ms;
};

//! Internal structure of an alpha-shaped synaptic input
typedef struct alpha_state_t {
    input_t lin_buff;           //!< buffer for linear term
    input_t exp_buff;           //!< buffer for exponential term
    //! _&tau;_<sup>-1</sup> pre-multiplied by d<i>t</i>
    input_t dt_divided_by_tau_sqr;
    decay_t decay;              //!< Exponential decay multiplier
    input_t q_buff;             //!< Temporary value of input
} alpha_state_t;

struct synapse_types_t {
	alpha_state_t exc;         //!< Excitatory synaptic input
	alpha_state_t inh;         //!< Inhibitory synaptic input
};

//! The supported synapse type indices
typedef enum {
    EXCITATORY,                 //!< Excitatory synaptic input
    INHIBITORY,                 //!< Inhibitory synaptic input
} synapse_alpha_input_buffer_regions;

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------

static inline void get_alpha_state(alpha_state_t *state, alpha_params_t *params,
		REAL time_step_ms, uint32_t n_steps_per_timestep) {
	REAL ts = kdivui(time_step_ms, n_steps_per_timestep);
	decay_t decay = expulr(-kdivk(ts, params->tau));
	decay_t init = kdivk(ts, (params->tau * params->tau));
	state->lin_buff = params->lin_init;
	state->exp_buff = params->exp_init;
	state->q_buff = params->q_init;
	state->dt_divided_by_tau_sqr = init;
	state->decay = decay;
}

static inline void synapse_types_initialise(synapse_types_t *state,
		synapse_types_params_t *params, uint32_t n_steps_per_timestep) {
	get_alpha_state(&state->exc, &params->exc, params->time_step_ms, n_steps_per_timestep);
	get_alpha_state(&state->inh, &params->inh, params->time_step_ms, n_steps_per_timestep);
}

static void synapse_types_save_state(synapse_types_t *state, synapse_types_params_t *params) {
	params->exc.lin_init = state->exc.lin_buff;
	params->exc.exp_init = state->exc.exp_buff;
	params->exc.q_init = state->exc.q_buff;
	params->inh.lin_init = state->inh.lin_buff;
	params->inh.exp_init = state->inh.exp_buff;
	params->inh.q_init = state->inh.q_buff;
}

//! \brief Applies alpha shaping to a parameter
//! \param[in,out] a_params: The parameter to shape
static inline void alpha_shaping(alpha_state_t* a_params) {
    a_params->lin_buff = a_params->lin_buff + (
    		a_params->q_buff * a_params->dt_divided_by_tau_sqr);

    // Update exponential buffer
    a_params->exp_buff = decay_s1615(a_params->exp_buff, a_params->decay);
}

//! \brief decays the stuff thats sitting in the input buffers as these have not
//!     yet been processed and applied to the neuron.
//!
//! This is to compensate for the valve behaviour of a synapse in biology
//! (spike goes in, synapse opens, then closes slowly)
//! plus the leaky aspect of a neuron.
//!
//! \param[in,out] parameters: the parameters to update
static inline void synapse_types_shape_input(
		synapse_types_t *parameters) {
    alpha_shaping(&parameters->exc);
    alpha_shaping(&parameters->inh);
}

//! \brief helper function to add input for a given timer period to a given
//!     neuron
//! \param[in] a_params: the parameter to update
//! \param[in] input: the input to add.
static inline void add_input_alpha(alpha_state_t *a_params, input_t input) {
    a_params->q_buff = input;

	a_params->exp_buff =
			decay_s1615(a_params->exp_buff, a_params->decay) + ONE;

    a_params->lin_buff =
            (a_params->lin_buff + (input * a_params->dt_divided_by_tau_sqr))
            * (ONE - kdivk(ONE, a_params->exp_buff));
}

//! \brief adds the inputs for a give timer period to a given neuron that is
//!     being simulated by this model
//! \details Add input from ring buffer. Zero if no spikes, otherwise one or
//!     more weights
//! \param[in] synapse_type_index: the type of input that this input is to be
//!     considered (aka excitatory or inhibitory etc)
//! \param[in,out] parameters: the parameters to update
//! \param[in] input: the inputs for that given synapse_type.
static inline void synapse_types_add_neuron_input(
        index_t synapse_type_index, synapse_types_t *parameters,
        input_t input) {
    if (input > ZERO) {
        switch (synapse_type_index) {
        case EXCITATORY:
            add_input_alpha(&parameters->exc, input);
            break;
        case INHIBITORY:
            add_input_alpha(&parameters->inh, input);
            break;
        }
    }
}

//! \brief extracts the excitatory input buffers from the buffers available
//!     for a given neuron ID
//! \param[in,out] excitatory_response: Buffer to put response in
//! \param[in] parameters: the pointer to the parameters to use
//! \return Pointer to array of excitatory input buffers for a given neuron ID.
static inline input_t* synapse_types_get_excitatory_input(
        input_t *excitatory_response, synapse_types_t *parameters) {
    excitatory_response[0] =
            parameters->exc.lin_buff * parameters->exc.exp_buff;
    return &excitatory_response[0];
}

//! \brief extracts the inhibitory input buffers from the buffers available
//!     for a given neuron ID
//! \param[in,out] inhibitory_response: Buffer to put response in
//! \param[in] parameters: the pointer to the parameters to use
//! \return Pointer to array of inhibitory input buffers for a given neuron ID.
static inline input_t* synapse_types_get_inhibitory_input(
        input_t *inhibitory_response, synapse_types_t *parameters) {
    inhibitory_response[0] =
            parameters->inh.lin_buff * parameters->inh.exp_buff;
    return &inhibitory_response[0];
}

//! \brief returns a human readable character for the type of synapse.
//! \details Examples would be `X` = excitatory types, `I` = inhibitory types,
//!     etc.
//! \param[in] synapse_type_index: the synapse type index
//!     (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static inline const char *synapse_types_get_type_char(
        index_t synapse_type_index) {
    switch (synapse_type_index) {
    case EXCITATORY:
        return "X";
    case INHIBITORY:
        return "I";
    default:
        log_debug("did not recognise synapse type %i", synapse_type_index);
        return "?";
    }
}

//! \brief prints the input for a neuron ID given the available inputs
//!     currently only executed when the models are in debug mode, as the prints
//!     are controlled from the synapses.c print_inputs() method.
//! \param[in] parameters: the pointer to the parameters to print
static inline void synapse_types_print_input(
        synapse_types_t *parameters) {
    io_printf(IO_BUF, "%12.6k - %12.6k",
            parameters->exc.lin_buff * parameters->exc.exp_buff,
            parameters->inh.lin_buff * parameters->inh.exp_buff);
}

//! \brief prints the parameters of the synapse type
//! \param[in] parameters: the pointer to the parameters to print
static inline void synapse_types_print_parameters(synapse_types_t *parameters) {
    log_debug("-------------------------------------\n");
    log_debug("exc_response  = %11.4k\n",
            parameters->exc.lin_buff * parameters->exc.exp_buff);
    log_debug("inh_response  = %11.4k\n",
            parameters->inh.lin_buff * parameters->inh.exp_buff);
}

#endif // _ALPHA_SYNAPSE_H_
