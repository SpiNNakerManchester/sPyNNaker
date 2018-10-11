#ifndef _TIMING_CEREBELLUM_IMPL_H_
#define _TIMING_CEREBELLUM_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef int16_t post_trace_t;
typedef int16_t pre_trace_t;

#include <neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_impl.h>
#include "timing.h"
#include <neuron/plasticity/stdp/weight_dependence/weight_one_term.h>

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>

//---------------------------------------
// Macros
//---------------------------------------
// Exponential decay lookup parameters
#define TAU_PLUS_TIME_SHIFT 0
#define EXP_SIN_LUT_SIZE 256

// Helper macros for looking up decays
#define EXP_SIN_LOOKUP(time) \
    maths_lut_exponential_decay( \
        time, TAU_PLUS_TIME_SHIFT, EXP_SIN_LUT_SIZE, exp_sin_lookup)
//#define DECAY_LOOKUP_TAU_MINUS(time) \
//    maths_lut_exponential_decay( \
//        time, TAU_MINUS_TIME_SHIFT, TAU_MINUS_SIZE, tau_minus_lookup)

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t exp_sin_lookup[EXP_SIN_LUT_SIZE];

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace() {
    return 0;
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {

	io_printf(IO_BUF, "Adding pre spike to event history (from climbing fibre)\n");

//    // Get time since last spike
//    uint32_t delta_time = time - last_time;

//    // Decay previous o1 and o2 traces
//    int32_t decayed_o1_trace = STDP_FIXED_MUL_16X16(last_trace,
//            DECAY_LOOKUP_TAU_MINUS(delta_time));

    // Add energy caused by new spike to trace
    // **NOTE** o2 trace is pre-multiplied by a3_plus
    int32_t new_o1_trace = 0; //decayed_o1_trace + STDP_FIXED_POINT_ONE;

//    log_debug("\tdelta_time=%d, o1=%d\n", delta_time, new_o1_trace);

    // Return new pre- synaptic event with decayed trace values with energy
    // for new spike added
    return (post_trace_t) new_o1_trace;
}

//---------------------------------------
static inline pre_trace_t timing_add_pre_spike(
        uint32_t time, uint32_t last_time, pre_trace_t last_trace) {


    return (pre_trace_t) 0; //new_r1_trace;
}

//---------------------------------------
static inline update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(last_pre_time);
    use(&last_pre_trace);

    // Here we will potentiate by the fixed amount alpha
    io_printf(IO_BUF, "    This is where we'll do potentiation\n");

    return weight_one_term_apply_potentiation(previous_state, 0);



//
//    // Get time of event relative to last post-synaptic event
//    uint32_t time_since_last_post = time - last_post_time;
//    if (time_since_last_post > 0) {
//        int32_t decayed_o1 = STDP_FIXED_MUL_16X16(
//            last_post_trace, DECAY_LOOKUP_TAU_MINUS(time_since_last_post));
//
//        log_debug("\t\t\ttime_since_last_post_event=%u, decayed_o1=%d\n",
//                  time_since_last_post, decayed_o1);
//
//        // Apply depression to state (which is a weight_state)
//        return weight_one_term_apply_depression(previous_state, decayed_o1);
//
//
//
//
//
//
//
//    } else {
//        return previous_state;
//    }
}

//---------------------------------------
static inline update_state_t timing_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace);
    use(last_post_time);
    use(&last_post_trace);



//    // This is where we lookup the value of e^(-x) * sin(x)^20
//
//



//
//    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = last_pre_time; //time - last_pre_time;
    io_printf(IO_BUF, "        delta t = %u,    ", time_since_last_pre);

    if (time_since_last_pre < 255){


        uint32_t multiplier = EXP_SIN_LOOKUP(time_since_last_pre);

        io_printf(IO_BUF, "multiplier: %k (fixed = %u)\n", multiplier << 4, multiplier);

        return weight_one_term_apply_depression(previous_state, multiplier);


    }
//
	io_printf(IO_BUF, "        delta t = %u,    ", time_since_last_pre);
	io_printf(IO_BUF, "        out of LUT range - do nothing");

//    if (time_since_last_pre > 0) {
//        int32_t decayed_r1 = STDP_FIXED_MUL_16X16(
//            last_pre_trace, DECAY_LOOKUP_TAU_PLUS(time_since_last_pre));
//
//        log_debug("\t\t\ttime_since_last_pre_event=%u, decayed_r1=%d\n",
//                  time_since_last_pre, decayed_r1);
//
//        // Apply potentiation to state (which is a weight_state)
//        return weight_one_term_apply_potentiation(previous_state, decayed_r1);
//    } else {
        return previous_state;
    //}
}

#endif // _TIMING_CEREBELLUM_IMPL_H_
