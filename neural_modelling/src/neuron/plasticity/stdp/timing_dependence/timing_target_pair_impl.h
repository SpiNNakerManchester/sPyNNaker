/*
 * Below is the program trace to show how 3 variables evolve given 
 * targets at 10ms,20ms and a doublet at 30ms,31ms:
 *
 * 10 ms target              |  20 ms target              |  30 ms doublet             |  31 ms doublet
 * --------------------------|----------------------------|----------------------------|----------------------------
 *                           |                            |                            |  updateWeight=accumulator20
 * accumulator+=accumLast0   |  accumulator+=accumLast10  |  accumulator+=accumLast20  |  accumulator=0
 * accumLast=PSP10           |  accumLast=PSP20           |  accumLast=PSP30           |  accumLast=0
 *
 */



//---------------------------------------
// Typedefines
//---------------------------------------
//typedef int16_t post_trace_t;
typedef struct post_trace_t {
  uint8_t trace;
  uint8_t ap; // this is an actual neuron action potential, not a target time
} post_trace_t;

typedef int16_t pre_trace_t;

static uint32_t last_target_time = 0; // the last time a target passed through here

#include "../synapse_structure/synapse_structure_weight_target.h"

//#include "timing.h"

//#include "../synapse_structure/synapse_structure.h"

address_t timing_initialise(address_t address);
static post_trace_t timing_get_initial_post_trace();
static update_state_t timing_apply_post_spike(
    uint32_t time, post_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace, uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state);

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
    return (post_trace_t) {.trace = 0, .ap = 0};
}

//---------------------------------------
// This will apply an actual postsynaptic spike
// usefull variables:
// time          = postsynaptic (+ dendritic delay) or target spike time 
// last_pre_time = last presynaptic spike time
static inline update_state_t timing_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(last_pre_time);
    use(&last_pre_trace);
    use(last_post_time);
    use(&last_post_trace);

    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = time - last_pre_time;

    //if ((time>1000) && (time<1050))
    //io_printf(IO_BUF,"Inside timing_apply_post_spike at: %dms,   time_since_last_pre: %dms,   last_target_time: %dms\n", time, time_since_last_pre, last_target_time);

    if (time_since_last_pre > 0) // within time frame
    {

        // decayed state
        int32_t PSP = DECAY_LOOKUP_TAU_PLUS( time_since_last_pre) -
                      DECAY_LOOKUP_TAU_MINUS(time_since_last_pre);

        // io_printf(IO_BUF,"time_since_last_pre: %dms\n", time_since_last_pre);
        log_debug("\t\t\ttime_since_last_pre_event=%u, PSP=%d\n", 
                  time_since_last_pre, PSP);

        // if True, we have a doublet, end of learning pattern!
        if (((time - last_target_time) == 1) && (time > 1))
        {
            //io_printf(IO_BUF,"doublet at: %dms,  previous_state.accumulator: %d\n", time, previous_state.accumulator);
            
            // Apply potentiation to state (which is a weight_state) if positive
            if (previous_state.accumulator > 0)
            {
                previous_state.weight_state = weight_one_term_apply_potentiation(previous_state.weight_state, previous_state.accumulator);
            }
            // Apply depression to state (which is a weight_state) if negative
            else if (previous_state.accumulator < 0)
            {
                previous_state.weight_state = weight_one_term_apply_depression(previous_state.weight_state, previous_state.accumulator);
            }
            previous_state.accumulator = 0;
            previous_state.accumLast   = 0;
        }

        // it is not the end of a learning pattern
        else 
        {
            // add last synaptic update to accumulation
            previous_state.accumulator += previous_state.accumLast; 
            
            // if it is an actual spike output event; not target
            if (trace.ap > 0)
            {
                previous_state.accumLast = -1 * PSP;
            }
            // otherwise, it is a target output event
            else 
            {
                previous_state.accumLast = PSP;
            }
            
            //io_printf(IO_BUF,"Target spike time: %dms,   last_target_time: %dms\n", time, last_target_time);
            last_target_time = time; // update the target time
        }
    }
    
    return previous_state;
}

