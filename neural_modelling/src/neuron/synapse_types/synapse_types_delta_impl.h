#ifndef _SYNAPSE_TYPES_DELTA_IMPL_H_
#define _SYNAPSE_TYPES_DELTA_IMPL_H_

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 1
#define SYNAPSE_TYPE_COUNT 2

#include "../decay.h"
#include <debug.h>

//---------------------------------------
// Synapse parameters
//---------------------------------------
typedef struct synapse_param_t {
} synapse_param_t;

#include "synapse_types.h"

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------
static inline index_t _ex_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(0, neuron_index);
}

static inline index_t _in_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(1, neuron_index);
}


// Delta_shaping
//
// This is used to give a simple exponential decay to synapses.
//
// If we have combined excitatory/inhibitory synapses it will be
// because both excitatory and inhibitory synaptic time-constants
// (and thus propogators) are identical.
static inline void synapse_types_shape_input(input_t *input_buffers,
        index_t neuron_index, synapse_param_t** parameters) {
    use(parameters);
    input_buffers[_ex_offset(neuron_index)] = 0;
    input_buffers[_in_offset(neuron_index)] = 0;
}

static inline void synapse_types_add_neuron_input(input_t *input_buffers,
        index_t synapse_type_index, index_t neuron_index,
        synapse_param_t** parameters, input_t input) {
    use(parameters);
    input_buffers[synapse_types_get_input_buffer_index(synapse_type_index,
        neuron_index)] += input;
}

static inline input_t synapse_types_get_excitatory_input(
        input_t *input_buffers, index_t neuron_index) {
    return input_buffers[_ex_offset(neuron_index)];
}

static inline input_t synapse_types_get_inhibitory_input(
        input_t *input_buffers, index_t neuron_index) {
    return input_buffers[_in_offset(neuron_index)];
}

static inline const char *synapse_types_get_type_char(
        index_t synapse_type_index) {
    if (synapse_type_index == 0) {
        return "X";
    } else {
        return "I";
    }
}

static inline void synapse_types_print_input(
        input_t *input_buffers, index_t neuron_index) {
    io_printf(IO_BUF, "%12.6k - %12.6k",
              input_buffers[_ex_offset(neuron_index)],
              input_buffers[_in_offset(neuron_index)]);
}

#endif  // _SYNAPSE_TYPES_DELTA_IMPL_H_
