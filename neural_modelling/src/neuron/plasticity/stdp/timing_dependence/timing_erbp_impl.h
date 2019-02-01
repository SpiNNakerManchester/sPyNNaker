#ifndef _TIMING_ERBP_IMPL_H_
#define _TIMING_ERBP_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef int16_t post_trace_t;
typedef int16_t pre_trace_t;

#include <neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_and_trace_impl.h>
#include "timing.h"
#include <neuron/plasticity/stdp/weight_dependence/weight_one_term.h>
#include <neuron/models/neuron_model_lif_erbp_impl.h>
#include <neuron/synapses.h>

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
#define TAU_PLUS_SIZE 2048

#define TAU_MINUS_TIME_SHIFT 0
#define TAU_MINUS_SIZE 0

// Helper macros for looking up decays
#define DECAY_LOOKUP_TAU_PLUS(time) \
    maths_lut_exponential_decay( \
        time, TAU_PLUS_TIME_SHIFT, TAU_PLUS_SIZE, tau_plus_lookup)
/* #define DECAY_LOOKUP_TAU_MINUS(time) \
    maths_lut_exponential_decay( \
        time, TAU_MINUS_TIME_SHIFT, TAU_MINUS_SIZE, tau_minus_lookup)
*/

//---------------------------------------
// Externals
//---------------------------------------
extern int16_t tau_plus_lookup[TAU_PLUS_SIZE];
//extern int16_t tau_minus_lookup[TAU_MINUS_SIZE];

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace() {
    return 0;
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
	use(&last_trace);

    // Get time since last spike
    uint32_t delta_time = time - last_time;

//    // Decay previous o1 and o2 traces
//    int32_t decayed_o1_trace = STDP_FIXED_MUL_16X16(last_trace,
//            DECAY_LOOKUP_TAU_MINUS(delta_time));
    int32_t decayed_o1_trace = 0;
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
        uint32_t time, uint32_t last_time, pre_trace_t last_trace,
		neuron_pointer_t neuron) {

	REAL mem_potential = neuron->V_membrane;
	REAL threshold_potential = -50k;
	REAL gamma = 0.3;
	REAL m = 0.02; // this factor already includes gamma
	REAL p_j;
	REAL limit = threshold_potential - neuron->V_rest;


	// Calculate p_j(V) using the triangle function
	if (mem_potential > threshold_potential) { // above threshold (centerline)
		if ((mem_potential - threshold_potential) > limit){
			p_j = 0;
		} else {
			p_j = gamma - (mem_potential - threshold_potential) * m;
		}
	} else { // below centerline
		if ((threshold_potential - mem_potential) > limit) {
			p_j = 0;
		} else{
			p_j = (mem_potential - neuron->V_rest) * m;
		}
	}

	io_printf(IO_BUF, "Voltage at time of pre spike: %k\n", mem_potential);
	io_printf(IO_BUF, "p_j at time of pre spike: %k\n", p_j);

	REAL to_add_to_trace = (p_j * STDP_FIXED_POINT_ONE) ;
	int32_t bits_to_add = bitsk(to_add_to_trace) >> 15;

	io_printf(IO_BUF, "Multiplication: %k\n", to_add_to_trace);
	io_printf(IO_BUF, "Multiplication: %u\n", bits_to_add);

    // Get time since last spike
    uint32_t delta_time = time - last_time;

    // Decay previous r1 and r2 traces
    int32_t decayed_r1_trace = STDP_FIXED_MUL_16X16(
        last_trace, DECAY_LOOKUP_TAU_PLUS(delta_time));

    // now scale STDP_FIXED_POINT_ONE by p_j(t), and multiply
    // Add energy caused by new spike to trace
    int32_t new_r1_trace = decayed_r1_trace + to_add_to_trace; // !!! NEED TO CHECK THIS MULTIPLY !!!

    io_printf(IO_BUF, "\tdelta_time=%u, r1=%d\n", delta_time, new_r1_trace);

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
    use(&last_post_trace);

    // Get time of event relative to last post-synaptic event
    uint32_t time_since_last_post = time - last_post_time;
    if (time_since_last_post > 0) {
//        int32_t decayed_o1 = STDP_FIXED_MUL_16X16(
//            last_post_trace, DECAY_LOOKUP_TAU_MINUS(time_since_last_post));
    	int32_t decayed_o1 = 0;
        log_debug("\t\t\ttime_since_last_post_event=%u, decayed_o1=%d\n",
                  time_since_last_post, decayed_o1);

        // Apply depression to state (which is a weight_state)

        previous_state.weight_state = weight_one_term_apply_depression(
        		previous_state.weight_state, decayed_o1);

        return previous_state;
    } else { // the else is now redundant
        return previous_state;
    }
}

//---------------------------------------
static inline update_state_t timing_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state) {
    use(&trace); // this contains the error
    use(last_post_time); // this contains the post time
    use(&last_post_trace);

    weight_t weight = (weight_t) trace;

    // Maybe need this to convert scaled weight to real units?
    input_t w = synapses_convert_weight_to_input(
    		weight,
			previous_state.weight_state.weight_region->weight_shift
			);



    // Here we decay the pre trace to the time of the error spike, and then
    // multiply it by the weight of the error spike (which we'd stored in the
    //postsynaptic event history)

    io_printf(IO_BUF, "Error value from apply post: %u\n", trace);
    io_printf(IO_BUF, "Error value from apply post: %k\n", w);

    io_printf(IO_BUF, "Shift: %u\n", previous_state.weight_state.weight_region->weight_shift);


    // Get time of event relative to last pre-synaptic event
    uint32_t time_since_last_pre = time - last_pre_time;
    if (time_since_last_pre > 0) {

    	// This allows us to decay the pre trace to the time of the error spike
        int32_t decayed_r1 = STDP_FIXED_MUL_16X16(
            last_pre_trace, DECAY_LOOKUP_TAU_PLUS(time_since_last_pre));

        uint32_t error_by_trace = (decayed_r1 * weight) >> (16 -
        		(previous_state.weight_state.weight_region->weight_shift + 1));

        io_printf(IO_BUF, "                time_since_last_pre_event=%u, "
        		"decayed_eligibility_trace=%d, mult_by_err=%u\n",
                  time_since_last_pre, decayed_r1, error_by_trace);

        // Apply potentiation to state (which is a weight_state)
        previous_state.weight_state = weight_one_term_apply_potentiation(previous_state.weight_state, error_by_trace);
    }
    return previous_state;
}

#endif // _TIMING_ERBP_IMPL_H_
