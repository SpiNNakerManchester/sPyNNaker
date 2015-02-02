#ifndef _SYNAPSES_H_
#define _SYNAPSES_H_

#include "../common/neuron-typedefs.h"
#include "synapse_row.h"

// Get the index of the ring buffer for a given timestep, synapse type and
// neuron index
static inline index_t synapses_get_ring_buffer_index(
        uint32_t simuation_timestep, uint32_t synapse_type_index,
        uint32_t neuron_index) {
    return (((simuation_timestep & SYNAPSE_DELAY_MASK)
             << SYNAPSE_TYPE_INDEX_BITS)
            | (synapse_type_index << SYNAPSE_INDEX_BITS)
            | neuron_index);
}

// Get the index of the ring buffer for a given timestep and combined
// synapse type and neuron index (as stored in a synapse row)
static inline index_t synapses_get_ring_buffer_index_combined(
        uint32_t simulation_timestep, uint32_t combined_synapse_neuron_index) {
    return (((simulation_timestep & SYNAPSE_DELAY_MASK)
             << SYNAPSE_TYPE_INDEX_BITS)
            | combined_synapse_neuron_index);
}

bool synapses_initialise(address_t address, uint32_t n_neurons,
                         input_t **input_buffers_value,
                         uint32_t **ring_buffer_to_input_buffer_left_shifts);

void synapses_do_timestep_update(timer_t time);

void synapses_process_synaptic_row(uint32_t time, synaptic_row_t row,
                                   bool write, uint32_t process_id);

void synapses_print_saturation_count();

#endif // _SYNAPSES_H_
