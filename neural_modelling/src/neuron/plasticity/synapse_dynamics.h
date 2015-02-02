#ifndef _SYNAPSE_DYNAMICS_H_
#define _SYNAPSE_DYNAMICS_H_

#include "../../common/neuron-typedefs.h"
#include "../synapse_row.h"

bool synapse_dynamics_initialise(
    address_t address, uint32_t n_neurons,
    uint32_t *ring_buffer_to_input_buffer_left_shifts);

void synapse_dynamics_process_plastic_synapses(
    address_t plastic_region_address, address_t fixed_region_address,
    weight_t *ring_buffers, uint32_t time);

void synapse_dynamics_process_post_synaptic_event(
    uint32_t time, index_t neuron_index);

input_t synapse_dynamics_get_intrinsic_bias(index_t neuron_index);

#endif // _SYNAPSE_DYNAMICS_H_
