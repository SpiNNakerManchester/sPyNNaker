#ifndef _TIMING_H_
#define _TIMING_H_

#include "../synapse_structure/synapse_structure.h"
#include "../../../models/neuron_model.h"
#include "../../../additional_inputs/additional_input.h"

address_t timing_initialise(address_t address);

static post_trace_t timing_get_initial_post_trace();

static post_trace_t timing_add_post_spike(uint32_t time, uint32_t last_time,
                                          post_trace_t last_trace);

static pre_trace_t timing_add_pre_spike(uint32_t time, uint32_t last_time,
                                        pre_trace_t last_trace);

static update_state_t timing_apply_pre_spike(
    uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace,  uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state,
	neuron_pointer_t post_synaptic_neuron,
	additional_input_pointer_t post_synaptic_additional_input);

static update_state_t timing_apply_post_spike(
    uint32_t time, post_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace, uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state, neuron_pointer_t post_synaptic_neuron);

#endif // _TIMING_H_
