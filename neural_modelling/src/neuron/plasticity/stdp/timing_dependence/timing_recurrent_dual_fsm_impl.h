#ifndef _TIMING_RECURRENT_DUAL_FSM_IMPL_H_
#define _TIMING_RECURRENT_DUAL_FSM_IMPL_H_

//---------------------------------------
// Typedefines
//---------------------------------------
typedef uint16_t post_trace_t;
typedef uint16_t pre_trace_t;

#include <neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_accumulator_impl.h>

#include "timing.h"
#include <neuron/plasticity/stdp/weight_dependence/weight_one_term.h>

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>
#include "random_util.h"

typedef struct {
    int32_t accum_decay_per_ts;
    int32_t accum_dep_plus_one[4];
    int32_t accum_pot_minus_one[4];
    int32_t pre_window_tc[4];
    int32_t post_window_tc[4];
} plasticity_params_recurrent_t;

static inline weight_state_t weight_one_term_apply_potentiation_sd(weight_state_t state,
                                                uint32_t syn_type, int32_t potentiation);
static inline weight_state_t weight_two_term_apply_potentiation_sd(weight_state_t state,
                                  accum v_diff, uint32_t syn_type, int32_t potentiation);
static inline weight_state_t weight_one_term_apply_depression_sd(weight_state_t state,
                                                  uint32_t syn_type, int32_t depression);
static inline weight_t weight_update_add( weight_state_t state);
static inline weight_t weight_update_sub( weight_state_t state);

//---------------------------------------
// Externals
//---------------------------------------
extern uint16_t pre_exp_dist_lookup_excit[STDP_FIXED_POINT_ONE];
extern uint16_t post_exp_dist_lookup_excit[STDP_FIXED_POINT_ONE];
extern uint16_t pre_exp_dist_lookup_excit2[STDP_FIXED_POINT_ONE];
extern uint16_t post_exp_dist_lookup_excit2[STDP_FIXED_POINT_ONE];
extern uint16_t pre_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE];
extern uint16_t post_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE];
extern uint16_t pre_exp_dist_lookup_inhib2[STDP_FIXED_POINT_ONE];
extern uint16_t post_exp_dist_lookup_inhib2[STDP_FIXED_POINT_ONE];
extern plasticity_params_recurrent_t recurrent_plasticity_params;

static uint32_t last_event_time;

extern uint32_t last_spike;

extern uint32_t recurrentSeed[4];

//extern accum *last_voltage;
//extern accum *voltage_before_last_spike;
extern threshold_type_pointer_t threshold_type_array;

// How muany right shifts to apply to the voltage difference. This is set to 4. Why?
// We assume a 16mV swing from resting potential to Vthresh. So a value of v_diff of 16mV
// is translated into a multiplier of 1. Any lesser value for v_diff will scale the 
// multiplier in the potentiation rule by a value less than 1. (In fact the difference
// between rest and threshold is 20mV (in this model) so this will not be exact, but
// a multiple of 2 is convenient to calculate).

#define full_v_scale_shift 4

#define ACCUM_SCALING	10
// With cycle time 35ms, timestep 0.2ms and goal of forgetting an accum update in 6 cycles,
// this means accum must drain in 210 ms, or 1050 timesteps, so set one step for accum to 1024
// to approximate this value.
#define ACC_DECAY_SCALING  5

//---------------------------------------
// Timing dependence inline functions
//---------------------------------------
static inline post_trace_t timing_get_initial_post_trace() {
    return 0;
}

//---------------------------------------
static inline post_trace_t timing_add_post_spike(
        uint32_t time, uint32_t last_time, post_trace_t last_trace) {
	use(&time);
	use(&last_time);
	use(&last_trace);
	// can't create post windows here, as don't have access to synapse type.

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
   if (syn_type == 0)
      window_length = pre_exp_dist_lookup_excit[random];
   else if (syn_type == 1)
      window_length = pre_exp_dist_lookup_excit2[random];
   else if (syn_type == 2)
      window_length = pre_exp_dist_lookup_inhib[random];
   else
      window_length = 50;   // 10ms at 0.2 ms timestep
      //window_length = pre_exp_dist_lookup_inhib2[random];
    // Return window length
    return window_length;
}

//---------------------------------------
// For inhib1-type synapses, this always reduces the weight.
// For other synapse types, this performs three functions:
// 1) Decay the accumulator value. Long periods with no spikes should cause the state to forget as this
//    will not correspond to a complete set of pattern repeats.
// 2) Set the flag for pre_waiting_post (we've got a pre-spike so now waiting for a post -pike)
// 3) Check if there was a post-spike window open at the time that this pre-spike was detected
//    in which case we decrement the accumulator and perhaps perform synaptic depression.

static inline update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state,
        uint32_t syn_type,
		neuron_pointer_t post_synaptic_neuron,
		additional_input_pointer_t post_synaptic_additional_input,
        threshold_type_pointer_t post_synaptic_threshold){

    use(&trace);
    use(&last_pre_time);
    use(&last_pre_trace);
    use(&last_post_trace);
    use(&syn_type);
    use(&post_synaptic_neuron);
    use(&post_synaptic_additional_input);
    use(&post_synaptic_threshold);

    // Decay accum value so that long periods without spikes cause it to forget:
    uint32_t time_since_last_event = time - last_event_time;

    //// For inhib2-type synapses, always decay the weight a little:
    //if (syn_type == 3) {
    //   previous_state.weight_state.weight -= (accum) 0.01;
    //}

    // Param accum_decay_per_ts is actually per 32 time steps now, to avoid rounding to zero errors:
    int32_t acc_change = (recurrent_plasticity_params.accum_decay_per_ts * time_since_last_event>>5);
    //log_info("Acc step: %d,  time: %d, +/-: %d", recurrent_plasticity_params.accum_decay_per_ts, time_since_last_event, acc_change);
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

    // Debug:
    // Check windows for syn_type 3 (inhibitory 2) which has special properties:
    if (syn_type == 3) {
       previous_state.weight_state.weight = weight_update_sub(previous_state.weight_state);
       //log_info("D-");
       // If we are inside a post-pre window, perform additive potentiation:
       if (time < previous_state.longest_post_pre_window_closing_time) {
          previous_state.weight_state.weight = weight_update_add(previous_state.weight_state);
          //log_info("D+");
       }
       return previous_state;
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
             //## previous_state.weight_state = weight_one_term_apply_depression_sd( previous_state.weight_state,
             //##                                                                    syn_type, STDP_FIXED_POINT_ONE);
            }
       }
       // Set the post window to be just before this pre-spike. This is the only way I've found to
       // reset it. It means that the first window length will be garbage.
       previous_state.longest_post_pre_window_closing_time = time - 1;
       previous_state.pre_waiting_post = true;

    return previous_state;
}

// This routine has different functionality depending on synapse type.
// For inhib-2-type synapses, it performs potentiation if the pre/post
// pair occur close together. This subroutine is concerned only with the pre-post pair.
// For other types it has two major responsibilities:
// 1) Generate the window size for this post spike and extend the window closure time
//    if this is beyond the current value. This is used by a following pre-spike for depression
// 2) Check if there is currently a pre-window open and then check if the post-spike is within
//    it. If so:
//               a) increment the accumulator
//               b) perform potentiation and reset accumulator if it has reached threshold
//               c) set the pre_found_post flag, equivalent to clearing the pore_waiting_post
//                  state machine back to idle (later post spikes will not cause an accum increment
//                  until a new pre-spike has arrived).
static inline update_state_t timing_apply_post_spike(

   uint32_t time, post_trace_t trace, uint32_t last_pre_time,
   pre_trace_t last_pre_trace, uint32_t last_post_time,
   post_trace_t last_post_trace, update_state_t previous_state,
    uint32_t syn_type,
   neuron_pointer_t post_synaptic_neuron,
   additional_input_pointer_t post_synaptic_additional_input,
   threshold_type_pointer_t post_synaptic_threshold, input_t post_synaptic_mem_V) {
   use(&trace);
   use(&last_post_time);
   use(&last_post_trace);
   use(&syn_type);
   use(&post_synaptic_neuron);
   use(&post_synaptic_additional_input);
   //use(&post_synaptic_threshold);
   //use(&post_synaptic_mem_V);

   // How far was the neuron from threshold just before the teaching signal arrived?
   accum voltage_difference = post_synaptic_threshold->threshold_value - post_synaptic_mem_V;

   // Voltage difference will be rectified (so no negative values allowed):
   if (voltage_difference < (accum)0.0) {
      voltage_difference = (accum)0.0;
   }

   //log_info("Thr: %k, postV: %k", post_synaptic_threshold->threshold_value, post_synaptic_mem_V);

   // log_info("Post_synaptic_potential from within apply post spike: %k", post_synaptic_mem_V);

   // Generate a windw size for this post-spike and extend the post window if it is
   // beyond the current value:
   uint32_t random = mars_kiss64_seed(recurrentSeed) & (STDP_FIXED_POINT_ONE - 1);
   uint16_t window_length;
   if (syn_type == 0)
      window_length = post_exp_dist_lookup_excit[random];
   else if (syn_type == 1)
      window_length = post_exp_dist_lookup_excit2[random];
   else if (syn_type == 2)
      window_length = post_exp_dist_lookup_inhib[random];
   else{
      //window_length = 50;  // 10ms @ 0.2 ms timestep
      window_length = post_exp_dist_lookup_inhib2[random];
   }

   uint32_t this_window_close_time = time + window_length;

   // Check if this post-spike extends the open window:
   if (previous_state.longest_post_pre_window_closing_time < this_window_close_time) {
      previous_state.longest_post_pre_window_closing_time = this_window_close_time;
   }

   // Get time of event relative to last pre-synaptic event
   uint32_t time_since_last_pre = time - last_pre_time;

   // For inhib-2-type (ID of 3) synapses, if we're inside the pre-post window
   // perform potentiation:
   if ((syn_type == 3) && (time_since_last_pre < last_pre_trace)) {
         previous_state.weight_state.weight = weight_update_add(previous_state.weight_state);
      //log_info("P+");
      return previous_state;
   }

    // Debug:
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
             //previous_state.accumulator = 0;
             // Set accum to a sub-threshold value, so that two potentiations in quick 
             // succession are less likely:
             previous_state.accumulator = 0;
             // SD Only update weight if we are not yet getting enough potential
             // to fire neuron without teaching input:
             //log_debug("Current V = %12.6k, V_hist = %12.6k",
                   //post_synaptic_neuron->V_membrane, post_synaptic_neuron->V_mem_hist);
             //log_debug("Threshhold value = %12.6k", post_synaptic_threshold->threshold_value);
             //log_info("Prev_V: %k", post_synaptic_mem_V);
             if (previous_state.weight_state.weight == (accum)0.0) {
                if (voltage_difference > (accum) 0.5) {
                   // Make a full weight increment:
                   previous_state.weight_state = weight_one_term_apply_potentiation_sd(previous_state.weight_state,
                                                            syn_type, STDP_FIXED_POINT_ONE);
                }
                else {
                   // Weight is to be used, but we don't want or need a full weight increment.
                   // make a tiny weight change so that this weight does not get used again until it decays:
                   previous_state.weight_state.weight = 1000; // Smallest posiive weight.
                }
             }

             //previous_state.weight_state = weight_two_term_apply_potentiation_sd(previous_state.weight_state,
             //                                         voltage_difference, syn_type, STDP_FIXED_POINT_ONE);
         }
      }
   }
   return previous_state;
}

static inline weight_t weight_update_add( weight_state_t state) {
   int32_t new_weight = state.weight + state.weight_region->a2_plus;
   if (new_weight > state.weight_region->max_weight) {
      new_weight = state.weight_region->max_weight;
   }
   return (weight_t) new_weight;
}

static inline weight_t weight_update_sub( weight_state_t state) {
   int32_t new_weight = state.weight - state.weight_region->a2_minus;
   if (new_weight < state.weight_region->min_weight) {
      new_weight = state.weight_region->min_weight;
   }
   return (weight_t) new_weight;
}

static inline weight_state_t weight_one_term_apply_potentiation_sd(
   weight_state_t state, uint32_t syn_type, int32_t potentiation) {
   use(&syn_type);
   int32_t scale = maths_fixed_mul16(
                   state.weight_region->max_weight - state.weight,
                   state.weight_region->a2_plus, state.weight_multiply_right_shift);

   // Multiply scale by potentiation and add
   // **NOTE** using standard STDP fixed-point format handles format conversion
   state.weight += STDP_FIXED_MUL_16X16(scale, potentiation);
   if (state.weight > state.weight_region->max_weight)
      state.weight = state.weight_region->max_weight;
   return state;
}

static inline weight_state_t weight_two_term_apply_potentiation_sd(
   weight_state_t state, accum v_diff, uint32_t syn_type, int32_t potentiation) {
   use(&syn_type);
   union accum_int {
       accum acc_interpretation;
       int32_t int_interpretation;
   };
       
   union accum_int scaled_v_diff;
   //accum scaled_v_diff;
   int32_t old_w = state.weight;
   //scaled_v_diff.acc_interpretation = v_diff >> full_v_scale_shift; // 16mV diff translates to scaled_v_diff = 1
   scaled_v_diff.acc_interpretation = v_diff * (accum)(1.0/18.0); // 18mV diff translates to scaled_v_diff = 1
   int32_t scale1 = maths_fixed_mul16(
                   state.weight_region->max_weight - state.weight,
                   state.weight_region->a2_plus, state.weight_multiply_right_shift);

   // Now scale the scale value further using the voltage difference between threshold and the
   // voltage at the soma just before the teaching signal:
   int32_t scale = scale1 * (int) scaled_v_diff.int_interpretation;
   scale = scale >> 15;

   // Multiply scale by potentiation and add
   // **NOTE** using standard STDP fixed-point format handles format conversion
   state.weight += scale;
   //if (1==1) {
       //log_info("Int: diff: %d, scaled_v_diff: %d    scale1: %d, scale: %d", v_diff, scaled_v_diff.int_interpretation, scale1, scale);
       //log_info("Max: %k, a2_plus: %k, shift: %d", state.weight_region->max_weight, state.weight_region->a2_plus, state.weight_multiply_right_shift);
       //log_info("shift: %d", state.weight_multiply_right_shift);
       //log_info("Diff: %k, scale1: %k, scale: %k oldW: %k, W: %k", v_diff, scale1, scale, old_w, state.weight);
   //} 
   return state;
}

static inline weight_state_t weight_one_term_apply_depression_sd(
   weight_state_t state, uint32_t syn_type, int32_t depression) {
   use(&syn_type);
   int32_t scale = maths_fixed_mul16(
                   state.weight - state.weight_region->min_weight,
                   state.weight_region->a2_minus, state.weight_multiply_right_shift);

    // Multiply scale by depression and subtract
    // **NOTE** using standard STDP fixed-point format handles format conversion
    state.weight -= STDP_FIXED_MUL_16X16(scale, depression);
    return state;
}

#endif  // _TIMING_RECURRENT_DUAL_FSM_IMPL_H_
