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

/*! \file
*
* \brief implementation of synapse_types.h for sEMD synapses.
*
* \details To be filled in...
*/

#ifndef _SYNAPSE_TYPES_SEMD_IMPL_H_
#define _SYNAPSE_TYPES_SEMD_IMPL_H_

//---------------------------------------
// Macros
//---------------------------------------
//! \brief Number of bits to encode the synapse type
//! \details <tt>ceil(log2(#SYNAPSE_TYPE_COUNT))</tt>
#define SYNAPSE_TYPE_BITS 2
//! \brief Number of synapse types
//! \details <tt>#NUM_EXCITATORY_RECEPTORS + #NUM_INHIBITORY_RECEPTORS</tt>
#define SYNAPSE_TYPE_COUNT 3

//! Number of excitatory receptors
#define NUM_EXCITATORY_RECEPTORS 2
//! Number of inhibitory receptors
#define NUM_INHIBITORY_RECEPTORS 1

#include <debug.h>
#include "synapse_types.h"
#include "exp_synapse_utils.h"

//---------------------------------------
// Synapse parameters
//---------------------------------------

struct synapse_types_params_t {
    exp_params_t exc;           //!< First excitatory synaptic input
    exp_params_t exc2;          //!< Second excitatory synaptic input
    exp_params_t inh;           //!< Inhibitory synaptic input
    //! Output scaling factor derived from first excitatory input
    input_t multiplicator_init;
    //! History storage used to reset synaptic state
    input_t exc2_old_init;
    //! Scaling factor for the secondary response
    input_t scaling_factor;
    //! The time step in milliseconds
    REAL timestep_ms;
};

struct synapse_types_t {
	exp_state_t exc;           //!< First excitatory synaptic input
	exp_state_t exc2;          //!< Second excitatory synaptic input
	exp_state_t inh;           //!< Inhibitory synaptic input
    //! Output scaling factor derived from first excitatory input
    input_t multiplicator;
    //! History storage used to reset synaptic state
    input_t exc2_old;
    //! Scaling factor for the secondary response
    input_t scaling_factor;
};

//! The supported synapse type indices
typedef enum {
    EXCITATORY_ONE,             //!< First excitatory synaptic input
    EXCITATORY_TWO,             //!< Second excitatory synaptic input
    INHIBITORY,                 //!< Inhibitory synaptic input
} synapse_semd_input_buffer_regions;


//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------

static inline void synapse_types_initialise(synapse_types_t *state,
		synapse_types_params_t *params, uint32_t n_steps_per_timestep) {
    decay_and_init(&state->exc, &params->exc, params->timestep_ms, n_steps_per_timestep);
    decay_and_init(&state->exc2, &params->exc2, params->timestep_ms, n_steps_per_timestep);
    decay_and_init(&state->inh, &params->inh, params->timestep_ms, n_steps_per_timestep);
    state->multiplicator = params->multiplicator_init;
	state->exc2_old = params->exc2_old_init;
	state->scaling_factor = params->scaling_factor;
}

static void synapse_types_save_state(synapse_types_t *state, synapse_types_params_t *params) {
	params->exc.init_input = state->exc.synaptic_input_value;
	params->exc2.init_input = state->exc2.synaptic_input_value;
	params->inh.init_input = state->inh.synaptic_input_value;
	params->multiplicator_init = state->multiplicator;
	params->exc2_old_init = state->exc2_old;
}

//! \brief decays the stuff thats sitting in the input buffers as these have not
//!     yet been processed and applied to the neuron.
//!
//! This is to compensate for the valve behaviour of a synapse in biology
//! (spike goes in, synapse opens, then closes slowly)
//! plus the leaky aspect of a neuron.
//!
//! \param[in,out] parameters: the pointer to the parameters to use
static inline void synapse_types_shape_input(synapse_types_t *parameters) {
	exp_shaping(&parameters->exc);
	exp_shaping(&parameters->exc2);
	exp_shaping(&parameters->inh);
}

//! \brief adds the inputs for a give timer period to a given neuron that is
//!     being simulated by this model
//! \param[in] synapse_type_index: the type of input that this input is to be
//!     considered (aka excitatory or inhibitory etc)
//! \param[in,out] parameter: the pointer to the parameters to use
//! \param[in] input: the input for that given synapse_type.
static inline void synapse_types_add_neuron_input(
        index_t synapse_type_index, synapse_types_t *parameter,
        input_t input) {
    switch (synapse_type_index) {
    case EXCITATORY_ONE:
    	add_input_exp(&parameter->exc, input);
    	break;
    case EXCITATORY_TWO:
    	add_input_exp(&parameter->exc2, input);
    	break;
    case INHIBITORY:
    	add_input_exp(&parameter->inh, input);
    	break;
    }
}

//! \brief extracts the excitatory input buffers from the buffers available
//!     for a given parameter set
//! \param[in,out] excitatory_response: Buffer to put response in
//! \param[in] parameters: the pointer to the parameters to use
//! \return the excitatory input buffers for a given neuron ID.
static inline input_t *synapse_types_get_excitatory_input(
        input_t *excitatory_response, synapse_types_t *parameters) {
	if (parameters->exc2.synaptic_input_value >= 0.001
	        && parameters->multiplicator == 0
			&& parameters->exc2_old == 0) {
		parameters->multiplicator = parameters->exc.synaptic_input_value;
	} else if (parameters->exc2.synaptic_input_value < 0.001) {
		parameters->multiplicator = 0;
	}

	parameters->exc2_old = parameters->exc2.synaptic_input_value;

    excitatory_response[0] = 0;
    excitatory_response[1] =
    		parameters->exc2.synaptic_input_value * parameters->multiplicator
    		* parameters->scaling_factor;
    return &excitatory_response[0];
}

//! \brief extracts the inhibitory input buffers from the buffers available
//!     for a given parameter set
//! \param[in,out] inhibitory_response: Buffer to put response in
//! \param[in] parameters: the pointer to the parameters to use
//! \return the inhibitory input buffers for a given neuron ID.
static inline input_t *synapse_types_get_inhibitory_input(
        input_t *inhibitory_response, synapse_types_t *parameters) {
    inhibitory_response[0] = parameters->inh.synaptic_input_value;
    return &inhibitory_response[0];
}

//! \brief returns a human readable character for the type of synapse.
//!     examples would be X = excitatory types, I = inhibitory types etc etc.
//! \param[in] synapse_type_index: the synapse type index
//!     (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static inline const char *synapse_types_get_type_char(
        index_t synapse_type_index) {
    switch (synapse_type_index) {
    case EXCITATORY_ONE:
        return "X1";
    case EXCITATORY_TWO:
        return "X2";
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
//! \param[in] parameters: the parameters to print
static inline void synapse_types_print_input(synapse_types_t *parameters) {
    log_info("%12.6k + %12.6k - %12.6k",
            parameters->exc.synaptic_input_value,
            parameters->exc2.synaptic_input_value,
            parameters->inh.synaptic_input_value);
    log_info("multiplicator = %11.4k\n", parameters->multiplicator);
    log_info("exc2_old      = %11.4k\n", parameters->exc2_old);
}

//! \brief printer call
//! \param[in] parameters: the pointer to the parameters to print
static inline void synapse_types_print_parameters(synapse_types_t *parameters) {
    log_info("exc_decay  = %11.4k\n", parameters->exc.decay);
    log_info("exc_init   = %11.4k\n", parameters->exc.init);
    log_info("exc2_decay = %11.4k\n", parameters->exc2.decay);
    log_info("exc2_init  = %11.4k\n", parameters->exc2.init);
    log_info("inh_decay  = %11.4k\n", parameters->inh.decay);
    log_info("inh_init   = %11.4k\n", parameters->inh.init);
    log_info("gsyn_excitatory_initial_value = %11.4k\n",
            parameters->exc.synaptic_input_value);
    log_info("gsyn_excitatory2_initial_value = %11.4k\n",
            parameters->exc2.synaptic_input_value);
    log_info("gsyn_inhibitory_initial_value = %11.4k\n",
            parameters->inh.synaptic_input_value);
    log_info("scaling_factor = %11.4k\n", parameters->scaling_factor);
}

#endif  // _SYNAPSE_TYPES_SEMD_IMPL_H_
