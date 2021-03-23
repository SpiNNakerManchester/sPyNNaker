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
 * \brief implementation of synapse_types.h for a delta decay to synapses.
 *
 * If we have combined excitatory/inhibitory synapses it will be
 * because both excitatory and inhibitory synaptic time-constants
 * (and thus propagators) are identical.
 */

#ifndef _SYNAPSE_TYPES_DELTA_IMPL_H_
#define _SYNAPSE_TYPES_DELTA_IMPL_H_

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

#include <debug.h>
#include <common/neuron-typedefs.h>
#include "synapse_types.h"

//---------------------------------------
// Synapse parameters
//---------------------------------------
//! A synaptic input shaped as a Dirac delta
typedef struct delta_params_t {
    //! The synaptic input value
    input_t synaptic_input_value;
} delta_params_t;

//! Delta synapses support just a single excitatory and inhibitory input each
struct synapse_param_t {
    delta_params_t exc; //!< Excitatory synaptic input
    delta_params_t inh; //!< Inhibitory synaptic input
};

//! The supported synapse type indices
typedef enum {
    EXCITATORY, //!< Excitatory synaptic input
    INHIBITORY, //!< Inhibitory synaptic input
} synapse_delta_input_buffer_regions;

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------

//! \brief Decays the stuff thats sitting in the input buffers.
//! \details
//!     In this case, a delta shape means returning the value to zero
//!     immediately.
//! \param[out] delta_param: the parameter to update
static inline void delta_shaping(delta_params_t *delta_param) {
	delta_param->synaptic_input_value = 0;
}

//! \brief decays the stuff thats sitting in the input buffers as these have not
//!     yet been processed and applied to the neuron.
//!
//! This is to compensate for the valve behaviour of a synapse in biology
//! (spike goes in, synapse opens, then closes slowly)
//! plus the leaky aspect of a neuron.
//!
//! \param[in,out] parameters: the pointer to the parameters to use
static inline void synapse_types_shape_input(
        synapse_param_t *parameters) {
	delta_shaping(&parameters->exc);
	delta_shaping(&parameters->inh);
}

//! \brief helper function to add input for a given timer period to a given
//!     neuron
//! \param[in,out] delta_param: the parameter to update
//! \param[in] input: the input to add.
static inline void add_input_delta(
        delta_params_t *delta_param, input_t input) {
	delta_param->synaptic_input_value += input;
}

//! \brief adds the inputs for a give timer period to a given neuron that is
//!     being simulated by this model
//! \param[in] synapse_type_index the type of input that this input is to be
//!     considered (aka excitatory or inhibitory etc)
//! \param[in,out] parameters: the pointer to the parameters to use
//! \param[in] input the inputs for that given synapse_type.
static inline void synapse_types_add_neuron_input(
        index_t synapse_type_index, synapse_param_t *parameters,
        input_t input) {
    switch (synapse_type_index) {
    case EXCITATORY:
    	add_input_delta(&parameters->exc, input);
    	break;
    case INHIBITORY:
    	add_input_delta(&parameters->inh, input);
    	break;
    }
}

//! \brief extracts the excitatory input buffers from the buffers available
//!     for a given parameter set
//! \param[in] parameters: the pointer to the parameters to use
//! \return the excitatory input buffers for a given neuron ID.
static inline input_t *synapse_types_get_excitatory_input(
        input_t *excitatory_response, synapse_param_t *parameters) {
    excitatory_response[0] = parameters->exc.synaptic_input_value;
    return &excitatory_response[0];
}

//! \brief extracts the inhibitory input buffers from the buffers available
//!     for a given parameter set
//! \param[in] parameters: the pointer to the parameters to use
//! \return the inhibitory input buffers for a given neuron ID.
static inline input_t *synapse_types_get_inhibitory_input(
        input_t *inhibitory_response, synapse_param_t *parameters) {
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
//! \param[in] parameters: the pointer to the parameters to use
static inline void synapse_types_print_input(
        synapse_param_t *parameters) {
    io_printf(IO_BUF, "%12.6k - %12.6k",
            parameters->exc.synaptic_input_value,
            parameters->inh.synaptic_input_value);
}

//! \brief printer call
//! \param[in] parameters: the pointer to the parameters to print
static inline void synapse_types_print_parameters(
        synapse_param_t *parameters) {
    synapse_types_print_input(parameters);
}

#endif  // _SYNAPSE_TYPES_DELTA_IMPL_H_
