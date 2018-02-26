#ifndef _SYNAPSE_DYNAMICS_H_
#define _SYNAPSE_DYNAMICS_H_

#include "../../common/neuron-typedefs.h"
#include "../synapse_row.h"

#include "../models/neuron_model.h"
#include "../additional_inputs/additional_input.h"
#include "../threshold_types/threshold_type.h"



bool synapse_dynamics_initialise(
    address_t address, uint32_t n_neurons,
    uint32_t *ring_buffer_to_input_buffer_left_shifts);

bool synapse_dynamics_process_plastic_synapses(
    address_t plastic_region_address, address_t fixed_region_address,
    weight_t *ring_buffers, uint32_t time);

void synapse_dynamics_process_post_synaptic_event(
    uint32_t time, index_t neuron_index);

input_t synapse_dynamics_get_intrinsic_bias(uint32_t time, index_t neuron_index);

void synapse_dynamics_print_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        uint32_t *ring_buffer_to_input_buffer_left_shifts);

//! \brief returns the counters for plastic pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return counters for plastic pre synaptic events or 0
uint32_t synapse_dynamics_get_plastic_pre_synaptic_events();

void synapse_dynamics_set_neuron_array(neuron_pointer_t neuron_array);

void synapse_dynamics_set_threshold_array(threshold_type_pointer_t threshold_type_array);

void synapse_dynamics_set_additional_input_array(
			additional_input_pointer_t additional_input_array);

#endif // _SYNAPSE_DYNAMICS_H_
