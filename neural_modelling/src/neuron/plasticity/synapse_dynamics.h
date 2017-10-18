#ifndef _SYNAPSE_DYNAMICS_H_
#define _SYNAPSE_DYNAMICS_H_

#include "../../common/neuron-typedefs.h"
#include "../synapse_row.h"
#include "../../common/sp_structs.h"

address_t synapse_dynamics_initialise(
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


//---------------------------------------
// Synaptic rewiring functions
//---------------------------------------

//! \brief  Searches the synaptic row for the the connection with the
//!         specified postsynaptic id
//! \return int32 representing the offset of the connection within the
//!         fixed region (this can be used to when removing the connection)
bool find_plastic_neuron_with_id(uint32_t id, address_t row, structural_plasticity_data_t *sp_data);
bool remove_plastic_neuron_at_offset(uint32_t offset, address_t row);
bool add_plastic_neuron_with_id(uint32_t id, address_t row, uint32_t weight,
                                uint32_t delay, uint32_t type);

#endif // _SYNAPSE_DYNAMICS_H_
