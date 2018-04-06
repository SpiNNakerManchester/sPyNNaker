#ifndef _SYNAPSE_STRUCTURE_H_
#define _SYNAPSE_STRUCTURE_H_

#include <weight.h>

static update_state_t synapse_structure_get_update_state(
        plastic_synapse_t synaptic_word, index_t synapse_type);

static final_state_t synapse_structure_get_final_state(
        update_state_t state);

static weight_t synapse_structure_get_final_weight(
        final_state_t final_state);

static plastic_synapse_t synapse_structure_get_final_synaptic_word(
        final_state_t final_state);

#endif // _SYNAPSE_STRUCTURE_H_
