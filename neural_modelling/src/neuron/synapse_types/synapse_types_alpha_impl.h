#ifndef _SYNAPSE_TYPES_ALPHA_IMPL_H_
#define _SYNAPSE_TYPES_ALPHA_IMPL_H_

// TODO: Needs to be fixed to work correctly!

//---------------------------------------
// Macros
//---------------------------------------
#define SYNAPSE_TYPE_BITS 2
#define SYNAPSE_TYPE_COUNT 4

#include "synapse_types.h"
#include "../decay.h"

//---------------------------------------
// Synapse shaping inline implementation
//---------------------------------------
static inline index_t _ex1_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(0, neuron_index);
}

static inline index_t _in1_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(1, neuron_index);
}

static inline index_t _ex2_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(2, neuron_index);
}

static inline index_t _in2_offset(index_t neuron_index) {
    return synapse_types_get_input_buffer_index(3, neuron_index);
}

static inline decay_t _ex1_decay(synapse_param_t *parameters,
        index_t neuron_index) {
    return (parameters[0][neuron_index].neuron_synapse_decay);
}

static inline decay_t _in1_decay(synapse_param_t *parameters,
        index_t neuron_index) {
    return (parameters[1][neuron_index].neuron_synapse_decay);
}

static inline decay_t _ex2_decay(synapse_param_t *parameters,
        index_t neuron_index) {
    return (parameters[2][neuron_index].neuron_synapse_decay);
}

static inline decay_t _in2_decay(synapse_param_t *parameters,
        index_t neuron_index) {
    return (parameters[3][neuron_index].neuron_synapse_decay);
}

// shape alpha:
//
// Default values (iaf_psc_alpha.cpp/iaf_cond_exp.c)
//
// tau_x = 2.0ms  0.2ms
// tau_i = 2.0ms  2.0ms
//
// h /* current time step size in ms */
//
// p11x = p22x = exp (-h/tau_x)
// p11i = p22i = exp (-h/tau_i)
//
// p21x = h * p11x
// p21i = h * p11i
//
// y2x  = p21x * y1x + p22x * y2x;
// y1x *= p11x
//
// y2i  = p21i * y1i + p22i * y2i;
// y1i *= p11i
//
// then add in current ring_buffer inputs..
//
// y1x += /* scale* ? */ ring [n, x]
// y1i +=/* scale* ? */  ring [n, i]
// with scale 1/tau_x or tau_i as approrpiate?

static inline void synapse_types_shape_input(input_t *input_buffers,
        index_t neuron_index, synapse_param_t** parameters) {
    input_buffers[_ex2_offset(neuron_index)] =
        decay_s1615(input_buffers[_ex1_offset(neuron_index)],
                    _ex1_decay(parameters, neuron_index))
        + decay_s1615(input_buffers[_ex2_offset(neuron_index)],
                      _ex2_decay(parameters, neuron_index));
    input_buffers[_in2_offset(neuron_index)] =
            decay_s1615(input_buffers[_in1_offset(neuron_index)],
                        _in1_decay(parameters, neuron_index))
            + decay_s1615(input_buffers[_in2_offset(neuron_index)],
                          _in2_decay(parameters, neuron_index));
}

static inline input_t synapse_types_get_excitatory_input(
        input_t *input_buffers, index_t neuron_index) {
    return input_buffers[_ex2_offset(neuron_index)];
}

static inline input_t synapse_types_get_inhibitory_input(
        input_t *input_buffers, index_t neuron_index) {
    return input_buffers[_in2_offset(neuron_index)];
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
    printf("%12.6k - %12.6k", input_buffers[_ex_offset(neuron_index)],
           input_buffers[_in_offset(neuron_index)]);
}

static inline void synapse_types_add_neuron_input(input_t *input_buffers,
        index_t synapse_type_index, index_t neuron_index,
        synapse_param_t** parameters, input_t input) {
    input_buffers[synapse_types_get_input_buffer_index(synapse_type_index,
        neuron_index)] += decay_s1615(input,
            parameters[synapse_type_index][neuron_index].neuron_synapse_init);
}
#endif  // _SYNAPSE_TYPES_ALPHA_IMPL_H_
