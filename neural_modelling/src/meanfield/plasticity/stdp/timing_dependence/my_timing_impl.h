#ifndef _MY_TIMING_H_
#define _MY_TIMING_H_

// These need to be defined before including any synapse stuff
#define SYNAPSE_TYPE_BITS 1
#define SYNAPSE_TYPE_COUNT 2

// TODO: Add any variables to be stored in the post trace structure
typedef struct post_trace_t {
} post_trace_t;

// TODO: Add any variables to be stored in the pre trace structure
typedef struct pre_trace_t {
} pre_trace_t;

// Because spin1_memcpy() is used in various places
#include <spin1_api.h>

// Include generic plasticity maths functions
#include <meanfield/plasticity/stdp/maths.h>

// TODO: Ensure the correct number of weight terms is chosen
#include <meanfield/plasticity/stdp/weight_dependence/weight_one_term.h>

// TODO: Choose the required synapse structure
#include <meanfield/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h>

#include <meanfield/plasticity/stdp/timing_dependence/timing.h>

// Include debug header for log_info etc
#include <debug.h>

// Note the parameters will be external
extern accum my_potentiation_parameter;
extern accum my_depression_parameter;

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace(void) {

    // TODO: Return the values required
    return (post_trace_t) {};
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    use(&last_time);
    use(&last_trace);

    log_debug("\tdelta_time=%u\n", time - last_time);

    // TODO: Perform operations when a new post-spike occurs

    // Return new pre- synaptic event with decayed trace values with energy
    // for new spike added
    return (post_trace_t) {};
}

//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {
    use(&last_time);
    use(&last_trace);

    log_debug("\tdelta_time=%u\n", time - last_time);

    // TODO: Perform operations when a new pre-spike occurs

    return (pre_trace_t ) {};
}

//---------------------------------------
static inline update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(&last_pre_time);
    use(&last_pre_trace);
    use(&last_post_trace);

    // TODO: Perform depression on pre spikes that occur after the
    // current spike
    accum time_since_last_post = (accum) (time - last_post_time);
    if (time_since_last_post > 0) {
        int32_t decayed_o1 = (int32_t)
                (time_since_last_post * my_depression_parameter);

        log_debug("\t\t\ttime_since_last_post=%k, decayed_o1=%d\n",
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
    use(&last_pre_trace);
    use(&last_post_time);
    use(&last_post_trace);

    // TODO: Perform potentiation on post spikes that occur after the
    // current spike
    accum time_since_last_pre = (accum) (time - last_pre_time);
    if (time_since_last_pre > 0) {
        int32_t decayed_r1 = (int32_t)
                (time_since_last_pre * my_potentiation_parameter);

        log_debug("\t\t\ttime_since_last_pre=%k, decayed_r1=%d\n",
                time_since_last_pre, decayed_r1);

        // Apply potentiation to state (which is a weight_state)
        return weight_one_term_apply_potentiation(previous_state, decayed_r1);
    } else {
        return previous_state;
    }
}

#endif // _MY_TIMING_H_
