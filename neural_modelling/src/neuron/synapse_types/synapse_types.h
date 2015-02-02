#ifndef _SYNAPSE_TYPES_H_
#define _SYNAPSE_TYPES_H_

#include "../../common/neuron-typedefs.h"
#include "../synapse_row.h"

static inline index_t synapse_types_get_input_buffer_index(
        index_t synapse_type_index, index_t neuron_index) {
    return ((synapse_type_index << SYNAPSE_INDEX_BITS) | neuron_index);
}

static void synapse_types_shape_input(
    input_t *input_buffers, index_t neuron_index, synapse_param_t** parameters);

static void synapse_types_add_neuron_input(
    input_t *input_buffers, index_t synapse_type_index, index_t neuron_index,
    synapse_param_t** parameters, input_t input);

static input_t synapse_types_get_excitatory_input(
    input_t *input_buffers, index_t neuron_index);

static input_t synapse_types_get_inhibitory_input(
    input_t *input_buffers, index_t neuron_index);

static const char *synapse_types_get_type_char(index_t synapse_type_index);

static void synapse_types_print_input(input_t *input_buffers, index_t neuron_index);

#endif // _SYNAPSE_TYPES_H_
