#ifndef _SYNAPSE_DYNAMICS_H_
#define _SYNAPSE_DYNAMICS_H_

#include "../../common/neuron-typedefs.h"
#include "../synapse_row.h"

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

#endif // _SYNAPSE_DYNAMICS_H_
