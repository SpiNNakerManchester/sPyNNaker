#ifndef VOGELS_2011_IMPL_H
#define VOGELS_2011_IMPL_H

//---------------------------------------
// Typedefines
//---------------------------------------
typedef int16_t post_trace_t;
typedef int16_t pre_trace_t;

#include "neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h"
#include "neuron/plasticity/stdp/timing_dependence/timing.h"
#include "neuron/plasticity/stdp/weight_dependence/weight_one_term.h"

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include "neuron/plasticity/common/maths.h"
#include "neuron/plasticity/common/stdp_typedefs.h"

//---------------------------------------
// Macros
//---------------------------------------
// Exponential decay lookup parameters
#define TAU_TIME_SHIFT 0
#define TAU_SIZE 256

// Helper macros for looking up decays
#define DECAY_LOOKUP_TAU(time) \
    maths_lut_exponential_decay(time, TAU_TIME_SHIFT, TAU_SIZE, tau_lookup)

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
    int32_t alpha;
} plasticity_trace_region_data_t;

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t tau_lookup[TAU_SIZE];
extern plasticity_trace_region_data_t plasticity_trace_region_data;

//---------------------------------------
// Declared functions
//---------------------------------------
uint32_t *plasticity_region_trace_filled(uint32_t* address, uint32_t flags);

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline int16_t timing_add_spike(uint32_t time, uint32_t last_time, int16_t last_trace)
{
    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous trace
    int32_t decayed_trace = STDP_FIXED_MUL_16X16(last_trace,
	    DECAY_LOOKUP_TAU(delta_time));

    // Add new spike to trace
    int32_t new_trace = decayed_trace + STDP_FIXED_POINT_ONE;

    log_debug("\tdelta_time=%d, new_trace=%d\n", delta_time, new_trace);
    return (int16_t)new_trace;
}

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace()
{
    return 0;
}
//---------------------------------------
static inline post_trace_t timing_add_post_spike(
    uint32_t time, uint32_t last_time, post_trace_t last_trace)
{
    return timing_add_spike(time, last_time, last_trace);
}
//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace)
{
    return timing_add_spike(time, last_time, last_trace);
}
//---------------------------------------
static inline update_state_t timing_apply_pre_spike(
    uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace, uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state)
{
    use(&trace);
    use(last_pre_time);
    use(&last_pre_trace);

    // Get time of event relative to last post-synaptic event
    uint32_t time_since_last_post = time - last_post_time;
    int32_t exponential_decay = DECAY_LOOKUP_TAU(time_since_last_post);
    int32_t decayed_o1 = STDP_FIXED_MUL_16X16(last_post_trace, exponential_decay)
	- plasticity_trace_region_data.alpha;

    log_debug("\t\t\ttime_since_last_post_event=%u, decayed_o1=%d\n",
	    time_since_last_post, decayed_o1);

    // Apply potentiation to state (which is a weight_state)
    return weight_one_term_apply_potentiation(previous_state, decayed_o1);

}
//---------------------------------------
static inline update_state_t timing_apply_post_spike(
    uint32_t time, post_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace, uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state)
{
    use(&trace);
    use(last_post_time);
    use(&last_post_trace);

    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = time - last_pre_time;
    int32_t exponential_decay = DECAY_LOOKUP_TAU(time_since_last_pre);
    int32_t decayed_r1 = STDP_FIXED_MUL_16X16(last_pre_trace, exponential_decay);

    log_debug("\t\t\ttime_since_last_pre_event=%u, decayed_r1=%d\n",
	    time_since_last_pre, decayed_r1);

    // Apply potentiation to state (which is a weight_state)
    return weight_one_term_apply_potentiation(previous_state, decayed_r1);
}

#endif  // VOGELS_2011_IMPL_H
