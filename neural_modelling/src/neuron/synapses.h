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

// Converts a weight stored in a synapse row to an input
static inline input_t synapses_convert_weight_to_input(weight_t weight,
                                                       uint32_t left_shift) {
    union {
        int_k_t input_type;
        s1615 output_type;
    } converter;

    converter.input_type = (int_k_t) (weight) << left_shift;

    return converter.output_type;
}

static inline void synapses_print_weight(weight_t weight, uint32_t left_shift) {
    if (weight != 0)
        log_debug("%12.6k", synapses_convert_weight_to_input(
            weight, left_shift));
    else
        log_debug("      ");
}

bool synapses_initialise(address_t address, uint32_t n_neurons,
                         input_t **input_buffers_value,
                         uint32_t **ring_buffer_to_input_buffer_left_shifts);

void synapses_do_timestep_update(timer_t time);

void synapses_process_synaptic_row(uint32_t time, synaptic_row_t row,
                                   bool write, uint32_t process_id,
                                   bool flush);

void synapses_print_saturation_count();

//! \either prints the counters for plastic and fixed pre synaptic events based
//! on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or does
//! nothing (the assumption being that a empty function will be removed by the
//! compiler and therefore there is no code bloat)
//! \return Nothing, this method does not return anything
void synapses_print_pre_synaptic_events();

#endif // _SYNAPSES_H_
