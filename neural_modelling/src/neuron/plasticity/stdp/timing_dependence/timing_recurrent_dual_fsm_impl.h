#ifndef _TIMING_RECURRENT_DUAL_FSM_IMPL_H_
#define _TIMING_RECURRENT_DUAL_FSM_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef uint16_t post_trace_t;
typedef uint16_t pre_trace_t;

#include "../synapse_structure/synapse_structure_weight_accumulator_impl.h"

#include "neuron/plasticity/stdp/timing_dependence/timing.h"
#include "neuron/plasticity/stdp/weight_dependence/weight_one_term.h"
#include "neuron/threshold_types/threshold_type_static.h"

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include "neuron/plasticity/common/maths.h"
#include "neuron/plasticity/common/stdp_typedefs.h"
#include "random.h"

typedef struct {
    int32_t accum_decay_per_ts;
    int32_t accum_dep_plus_one[2];
    int32_t accum_pot_minus_one[2];
    int32_t pre_window_tc[2];
    int32_t post_window_tc[2];
} plasticity_params_recurrent_t;

static inline weight_state_t weight_one_term_apply_potentiation_sd(weight_state_t state,
                                                uint32_t syn_type, int32_t potentiation);
static inline weight_state_t weight_one_term_apply_depression_sd(weight_state_t state,
                                                  uint32_t syn_type, int32_t depression);

//---------------------------------------
// Externals
//---------------------------------------
extern uint16_t pre_exp_dist_lookup[STDP_FIXED_POINT_ONE];
extern uint16_t post_exp_dist_lookup[STDP_FIXED_POINT_ONE];
extern uint16_t pre_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE];
extern uint16_t post_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE];
extern plasticity_params_recurrent_t recurrent_plasticity_params;

static uint32_t last_event_time;

extern uint32_t last_spike;

extern uint32_t recurrentSeed[4];

extern accum *last_voltage;
extern accum *voltage_before_last_spike;
extern threshold_type_pointer_t threshold_type_array;

#define ACCUM_SCALING	10
// With cycle time 35ms, timestep 0.2ms and goal of forgetting an accum update in 6 cycles,
// this means accum must drain in 210 ms, or 1050 timesteps, so set one step for accum to 1024
// to approximate this value.

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace() {
    return -9999;
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
    return 0; // Return window_length;
}

//---------------------------------------
static inline pre_trace_t timing_add_pre_spike_sd( uint32_t time, uint32_t last_time, 
                  pre_trace_t last_trace, uint32_t syn_type) {
    use(&time);
    use(&last_time);
    use(&last_trace);

    uint16_t window_length;
    last_event_time = last_time;

    // Pick random number and use to draw from exponential distribution
    uint32_t random = mars_kiss64_seed(recurrentSeed) & (STDP_FIXED_POINT_ONE - 1);
    if (syn_type == 0) {
       window_length = pre_exp_dist_lookup[random];       // Excit. synapse
    }
    else {
       window_length = pre_exp_dist_lookup_inhib[random]; // Inhib. synapse
    }
    // Return window length
    return window_length;
}

//---------------------------------------
// This performs three functions:
// 1) Decay the accumulator value. Long periods with no spikes should cause the state to forget as this
//    will not correspond to a complete set of pattern repeats.
// 2) Set the flag for pre_waiting_post (we've got a pre-spike so now waiting for a post -pike)
// 3) Check if there was a post-spike window open at the time that this pre-spike was detected
//    in which case we decrement the accumulator and perhaps perform synaptic depression.

static inline update_state_t timing_apply_pre_spike_sd(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state, uint32_t syn_type, uint32_t postNeuronIndex) {
    use(&trace);
    use(&last_pre_time);
    use(&last_pre_trace);

	// Decay accum value so that long periods without spikes cause it to forget:
    uint32_t time_since_last_event = time - last_event_time;

    int32_t acc_change = (recurrent_plasticity_params.accum_decay_per_ts * time_since_last_event)>>ACCUM_SCALING;
    if (previous_state.accumulator > 0) {
        previous_state.accumulator -= acc_change;
        if (previous_state.accumulator < 0) {
            previous_state.accumulator = 0;
        }
    } else if (previous_state.accumulator < 0) {
        previous_state.accumulator += acc_change;
        if (previous_state.accumulator > 0) {
            previous_state.accumulator = 0;
        }
    }
    // Check if there was a post window open when this pre arrived and if so,
    // trigger an accum decrement (a step towards synaptic depression):
    if ((time > last_post_time) && (time < previous_state.longest_post_pre_window_closing_time)) {
       // The pre-spike has occurred inside a post window.
       // Get time of event relative to last post-synaptic event
       uint32_t time_since_last_post = time - last_post_time;

       if (previous_state.accumulator >
          recurrent_plasticity_params.accum_dep_plus_one[syn_type]<<ACCUM_SCALING){
             // If accumulator's not going to hit depression limit, decrement it
             previous_state.accumulator = previous_state.accumulator - (1<<ACCUM_SCALING);
          } else {
             // Otherwise, reset accumulator and apply depression
             previous_state.accumulator = 0;
             previous_state.weight_state = weight_one_term_apply_depression_sd( previous_state.weight_state,
                                                                                syn_type, STDP_FIXED_POINT_ONE);
            }
       }
       // Set the post window to be just before this pre-spike. This is the only way I've found to
       // reset it. It means that the first window length will be garbage.
       previous_state.longest_post_pre_window_closing_time = time - 1;
       previous_state.pre_waiting_post = true;

    return previous_state;
}

// This routine has two major responsibilities:
// 1) Generate the window size for this post spike and extend the window closure time
// if this is beyond the current value. This is used by a following pre-spike for depression
// 2) Check if there is currently a pre-window open and then check if the post-spike is within
//    it. If so:
//               a) increment the accumulator 
//               b) perform potentiation and reset accumulator if it has reached threshold
//               c) set the pre_found_post flag, equivalent to clearing the pore_waiting_post 
//                  state machine back to idle (later post spikes will not cause an accum increment
//                  until a new pre-spike has arrived).
static inline update_state_t timing_apply_post_spike_sd(
   uint32_t time, post_trace_t trace, uint32_t last_pre_time,
   pre_trace_t last_pre_trace, uint32_t last_post_time,
   post_trace_t last_post_trace, update_state_t previous_state, uint32_t syn_type, uint32_t postNeuronIndex) {
   use(&trace);
   use(&last_post_time);
   use(&last_post_trace);

   // Generate a windw size for this post-spike and extend the post window if it is
   // beyond the current value:
   uint32_t random = mars_kiss64_seed(recurrentSeed) & (STDP_FIXED_POINT_ONE - 1);
   uint16_t window_length;
   if (syn_type == 0)
      window_length = post_exp_dist_lookup[random];
   else
      window_length = post_exp_dist_lookup_inhib[random];

   uint32_t this_window_close_time = time + window_length;

   // Check if this post-spike extends the open window:
   if (previous_state.longest_post_pre_window_closing_time < this_window_close_time) {
      previous_state.longest_post_pre_window_closing_time = this_window_close_time;
   }

   // Get time of event relative to last pre-synaptic event
   uint32_t time_since_last_pre = time - last_pre_time;

   // If spikes don't coincide:
   if (previous_state.pre_waiting_post == true && time_since_last_pre > 0) {
      previous_state.pre_waiting_post = false;

      // Now check if this post spike occurred in the open window created by the previous pre-spike:
      if (time_since_last_pre < last_pre_trace) {
         if (previous_state.accumulator < 
             recurrent_plasticity_params.accum_pot_minus_one[syn_type]<<ACCUM_SCALING){
             // If accumulator's not going to hit potentiation limit, increment it:
             previous_state.accumulator = previous_state.accumulator + (1<<ACCUM_SCALING);
         } else {
             previous_state.accumulator = 0;
             previous_state.weight_state = weight_one_term_apply_potentiation_sd(previous_state.weight_state,
                                                                        syn_type, STDP_FIXED_POINT_ONE);
         }
      }
   }
   return previous_state;
}

static inline weight_state_t weight_one_term_apply_potentiation_sd(
   weight_state_t state, uint32_t syn_type, int32_t potentiation) {

   int32_t scale = maths_fixed_mul16(
                   state.weight_region->max_weight - state.weight,
                   state.weight_region->a2_plus, state.weight_multiply_right_shift);

   // Multiply scale by potentiation and add
   // **NOTE** using standard STDP fixed-point format handles format conversion
   state.weight += STDP_FIXED_MUL_16X16(scale, potentiation);
   return state;
}

static inline weight_state_t weight_one_term_apply_depression_sd(
   weight_state_t state, uint32_t syn_type, int32_t depression) {

   int32_t scale = maths_fixed_mul16(
                   state.weight - state.weight_region->min_weight,
                   state.weight_region->a2_minus, state.weight_multiply_right_shift);

    // Multiply scale by depression and subtract
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight -= STDP_FIXED_MUL_16X16(scale, depression);
    return state;
}

#endif  // _TIMING_RECURRENT_DUAL_FSM_IMPL_H_
