#ifndef _TIMING_PAIR_IMPL_H_
#define _TIMING_PAIR_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef int16_t post_trace_t;
typedef int16_t pre_trace_t;

#include "../synapse_structure/synapse_structure_weight_impl.h"
#include "timing.h"
#include "../weight_dependence/weight_one_term.h"

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include "../../common/maths.h"
#include "../../common/stdp_typedefs.h"

//---------------------------------------
// Macros
//---------------------------------------
// Exponential decay lookup parameters
#define TAU_PLUS_TIME_SHIFT 0
#define TAU_PLUS_SIZE 256

#define TAU_MINUS_TIME_SHIFT 0
#define TAU_MINUS_SIZE 256

// Helper macros for looking up decays
#define DECAY_LOOKUP_TAU_PLUS(time) \
    maths_lut_exponential_decay( \
        time, TAU_PLUS_TIME_SHIFT, TAU_PLUS_SIZE, tau_plus_lookup)
#define DECAY_LOOKUP_TAU_MINUS(time) \
    maths_lut_exponential_decay( \
        time, TAU_MINUS_TIME_SHIFT, TAU_MINUS_SIZE, tau_minus_lookup)

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t tau_plus_lookup[TAU_PLUS_SIZE];
extern int16_t tau_minus_lookup[TAU_MINUS_SIZE];

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace() {
    return 0;
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {

    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous o1 and o2 traces
    int32_t decayed_o1_trace = STDP_FIXED_MUL_16X16(last_trace,
            DECAY_LOOKUP_TAU_MINUS(delta_time));

    // Add energy caused by new spike to trace
    // **NOTE** o2 trace is pre-multiplied by a3_plus
    int32_t new_o1_trace = decayed_o1_trace + STDP_FIXED_POINT_ONE;

    log_debug("\tdelta_time=%d, o1=%d\n", delta_time, new_o1_trace);

    // Return new pre- synaptic event with decayed trace values with energy
    // for new spike added
    return (post_trace_t) new_o1_trace;
}

//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {

    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous r1 and r2 traces
    int32_t decayed_r1_trace = STDP_FIXED_MUL_16X16(
        last_trace, DECAY_LOOKUP_TAU_PLUS(delta_time));

    // Add energy caused by new spike to trace
    int32_t new_r1_trace = decayed_r1_trace + STDP_FIXED_POINT_ONE;

    log_debug("\tdelta_time=%u, r1=%d\n", delta_time, new_r1_trace);

    // Return new pre-synaptic event with decayed trace values with energy
    // for new spike added
    return (pre_trace_t) new_r1_trace;
}

//---------------------------------------
static inline update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(last_pre_time);
    use(&last_pre_trace);

    // Get time of event relative to last post-synaptic event
    uint32_t time_since_last_post = time - last_post_time;
    if (time_since_last_post > 0) {
        int32_t decayed_o1 = STDP_FIXED_MUL_16X16(
            last_post_trace, DECAY_LOOKUP_TAU_MINUS(time_since_last_post));

        log_debug("\t\t\ttime_since_last_post_event=%u, decayed_o1=%d\n",
                  time_since_last_post, decayed_o1);

        // Apply depression to state (which is a weight_state)
        return weight_one_term_apply_depression(previous_state, decayed_o1);
    } else {
        return previous_state;
    }
}

//---------------------------------------
static inline update_state_t timing_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(last_post_time);
    use(&last_post_trace);

    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = time - last_pre_time;
    if (time_since_last_pre > 0) {
        int32_t decayed_r1 = STDP_FIXED_MUL_16X16(
            last_pre_trace, DECAY_LOOKUP_TAU_PLUS(time_since_last_pre));

        log_debug("\t\t\ttime_since_last_pre_event=%u, decayed_r1=%d\n",
                  time_since_last_pre, decayed_r1);

        // Apply potentiation to state (which is a weight_state)
        return weight_one_term_apply_potentiation(previous_state, decayed_r1);
    } else {
        return previous_state;
    }
}

#endif // _TIMING_PAIR_IMPL_H_
