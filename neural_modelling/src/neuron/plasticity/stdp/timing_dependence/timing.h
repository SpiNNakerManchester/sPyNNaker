#ifndef _TIMING_H_
#define _TIMING_H_

#include "../synapse_structure/synapse_structure.h"

address_t timing_initialise(address_t address);

static post_trace_t timing_get_initial_post_trace();

static post_trace_t timing_add_post_spike(uint32_t time, uint32_t last_time,
                                          post_trace_t last_trace);

static pre_trace_t timing_add_pre_spike(uint32_t time, uint32_t last_time,
                                        pre_trace_t last_trace);

static update_state_t timing_apply_pre_spike(
    uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace,  uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state);

static update_state_t timing_apply_post_spike(
    uint32_t time, post_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace, uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state);

static inline int32_t get_post_trace(int32_t trace);

static inline int32_t get_dopamine_trace(int32_t trace);

static inline int32_t trace_build(int32_t post_trace, int32_t dopamine_trace);


#endif // _TIMING_H_
