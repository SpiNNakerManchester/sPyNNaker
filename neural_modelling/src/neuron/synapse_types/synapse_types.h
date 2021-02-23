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

//! \dir
//! \brief Synaptic behaviour types
//! \file
//! \brief API for synaptic behaviour types
//! (see also \ref src/neuron/input_types)
#ifndef _SYNAPSE_TYPES_H_
#define _SYNAPSE_TYPES_H_

#include <common/neuron-typedefs.h>
#include <neuron/synapse_row.h>

// Forward declaration of real type
struct synapse_param_t;
typedef struct synapse_param_t synapse_param_t;

//! Forward declaration of synapse type (creates a definition for a pointer
//! to a synapse type parameter struct
typedef synapse_param_t *synapse_param_pointer_t;

//! \brief decays the stuff thats sitting in the input buffers
//! as these have not yet been processed and applied to the neuron.
//!
//! This is to compensate for the valve behaviour of a synapse
//! in biology (spike goes in, synapse opens, then closes slowly).
//! \param[in,out] parameters: the parameters to update
static void synapse_types_shape_input(synapse_param_t *parameters);

//! \brief adds the inputs for a give timer period to a given neuron that is
//!     being simulated by this model
//! \param[in] synapse_type_index: the type of input that this input is to be
//!     considered (aka excitatory or inhibitory etc)
//! \param[in,out] parameters: the parameters to update
//! \param[in] input: the inputs for that given synapse_type.
static void synapse_types_add_neuron_input(
        index_t synapse_type_index, synapse_param_t *parameters,
        input_t input);

//! \brief extracts the excitatory input buffers from the buffers available
//!     for a given neuron ID
//! \param[in] parameters: the pointer to the parameters to use
//! \return Pointer to array of excitatory input buffers for a given neuron ID.
static input_t* synapse_types_get_excitatory_input(
        input_t *excitatory_response, synapse_param_t *parameters);

//! \brief extracts the inhibitory input buffers from the buffers available
//!     for a given neuron ID
//! \param[in] parameters: the pointer to the parameters to use
//! \return Pointer to array of inhibitory input buffers for a given neuron ID.
static input_t* synapse_types_get_inhibitory_input(
        input_t *inhibitory_response, synapse_param_t *parameters);

//! \brief returns a human readable character for the type of synapse.
//!
//! Examples would be `X` = excitatory types, `I` = inhibitory types, etc.
//!
//! \param[in] synapse_type_index: the synapse type index
//!     (there is a specific index interpretation in each synapse type)
//! \return a human readable character representing the synapse type.
static const char *synapse_types_get_type_char(index_t synapse_type_index);

//! \brief prints the parameters of the synapse type
//! \param[in] parameters: the pointer to the parameters to print
static void synapse_types_print_parameters(
        synapse_param_t *parameters);

//! \brief prints the input for a neuron ID given the available inputs
//!     currently only executed when the models are in debug mode, as the prints
//!     are controlled from the synapses.c print_inputs() method.
//! \param[in] parameters: the pointer to the parameters to print
static void synapse_types_print_input(synapse_param_t *parameters);

#endif // _SYNAPSE_TYPES_H_
