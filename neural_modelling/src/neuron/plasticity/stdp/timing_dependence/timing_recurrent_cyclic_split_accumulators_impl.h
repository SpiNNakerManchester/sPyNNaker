#ifndef _TIMING_RECURRENT_CYCLIC_IMPL_H_
#define _TIMING_RECURRENT_CYCLIC_IMPL_H_

#define print_plasticity false
#define locked_weights_unchanged false

//---------------------------------------
// Typedefines
//---------------------------------------
typedef uint16_t post_trace_t;
typedef uint16_t pre_trace_t;

#include <neuron/plasticity/stdp/synapse_structure/synapse_structure_weight_accumulator_impl.h>
#include <neuron/threshold_types/threshold_type_static.h>

#include "timing.h"
#include <neuron/plasticity/stdp/weight_dependence/weight_one_term.h>

// Include debug header for log_info etc
#include <debug.h>

// Include generic plasticity maths functions
#include <neuron/plasticity/stdp/maths.h>
#include <neuron/plasticity/stdp/stdp_typedefs.h>
#include "random.h"
#include <neuron/models/neuron_model.h>
#include <neuron/models/neuron_model_lif_v_hist_impl.h>

extern neuron_pointer_t neuron_array;


#define inc_tune_pot +1
#define inc_tune_dep -1
#define inc_LL_dep -1

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

static uint32_t rndCountDep = 0; // SD!
static uint32_t rndYesCountDep = 0;
static uint32_t rndCountPot = 0; // SD!
static uint32_t rndYesCountPot = 0;
//---------------------------------------
// Externals
//---------------------------------------
extern uint16_t pre_exp_dist_lookup_excit[STDP_FIXED_POINT_ONE>>2];
extern uint16_t post_exp_dist_lookup_excit[STDP_FIXED_POINT_ONE>>2];
extern uint16_t pre_exp_dist_lookup_excit2[STDP_FIXED_POINT_ONE>>2];
extern uint16_t post_exp_dist_lookup_excit2[STDP_FIXED_POINT_ONE>>2];
extern uint16_t pre_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE>>2];
extern uint16_t post_exp_dist_lookup_inhib[STDP_FIXED_POINT_ONE>>2];
extern uint16_t pre_exp_dist_lookup_inhib2[STDP_FIXED_POINT_ONE>>2];
extern uint16_t post_exp_dist_lookup_inhib2[STDP_FIXED_POINT_ONE>>2];
extern plasticity_params_recurrent_t recurrent_plasticity_params;

static uint32_t last_event_time;

extern uint32_t last_spike;

extern uint32_t recurrentSeed[4];
extern int32_t random_enabled;
extern REAL v_diff_pot_threshold;

extern uint32_t global_weight_scale;

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

    // If enabled, pick random number and use to draw from exponential distribution
    uint32_t random;

    if (!random_enabled){
    		random = (STDP_FIXED_POINT_ONE>>3)-1;
    		if (print_plasticity){
    			io_printf(IO_BUF, "Random window generation disabled in timing_add_pre_spike\n");
    		}
    } else {
    	random = mars_kiss64_seed(recurrentSeed) &
    			((STDP_FIXED_POINT_ONE>>2) - 1);
    	if (print_plasticity){
    		io_printf(IO_BUF, "Random window generation enabled in timing_add_pre_spike\n");
    	}
    }

    if (print_plasticity){
    	io_printf(IO_BUF, "Random number: %u\n", random);
    }

    if      (syn_type == 0) window_length = pre_exp_dist_lookup_excit[random];
    else if (syn_type == 1) window_length = pre_exp_dist_lookup_excit2[random];
    else if (syn_type == 2) window_length = pre_exp_dist_lookup_inhib[random];
    else                    window_length = pre_exp_dist_lookup_inhib2[random];

   if (print_plasticity){
	   io_printf(IO_BUF, "Pre window length: %u\n", window_length);
   }
    // Return window length
    return window_length;
}

//---------------------------------------
// This performs three functions:
// 1) Decay the accumulator value. Long periods with no spikes should cause the state to forget as this
//    will not correspond to a complete set of pattern repeats.
// 2) Set the flag for pre_waiting_post (we've got a pre-spike so now waiting for a post-spike)
// 3) Check if there was a post-spike window open at the time that this pre-spike was detected
//    in which case we perform some kind of depression (depending on other factors):

static inline update_state_t timing_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_post_time,
        post_trace_t last_post_trace, update_state_t previous_state,
        uint32_t syn_type,
		neuron_pointer_t post_synaptic_neuron,
		additional_input_pointer_t post_synaptic_additional_input,
        threshold_type_pointer_t post_synaptic_threshold, input_t post_synaptic_mem_V){

    use(&trace);
    use(&last_pre_time);
    use(&last_pre_trace);
    use(&last_post_trace);
    use(&syn_type);
    //use(&post_synaptic_neuron);
    use(&post_synaptic_additional_input);
    use(&post_synaptic_threshold);


       uint32_t random;


       // How far was the neuron from threshold just before the teaching signal arrived?
       // Also extract flag indicating whether neuron was fired by presynaptic input (not Teacher!)
       accum voltage_difference;

       if (post_synaptic_mem_V > 900.0k) {
    	   // neuron was fired by presynaptic input
    	   voltage_difference = 1000.0k;
       } else {
    	   // neuron was fired by Teacher
    	   voltage_difference = post_synaptic_threshold->threshold_value - post_synaptic_mem_V;
       }

       // Voltage difference will be rectified (so no negative values allowed - can this ever happen?):
       if (voltage_difference < (accum)0.0) {
          voltage_difference = (accum)0.0;
       }


       if (!random_enabled) {
    	   random = (STDP_FIXED_POINT_ONE>>3)-1; //5;
    	   if (print_plasticity){
               io_printf(IO_BUF, "Random window generation disabled in timing_apply_post_spike\n");
    	   }
       } else {
    	   random = mars_kiss64_seed(recurrentSeed) & ((STDP_FIXED_POINT_ONE>>2) - 1);
    	   if (print_plasticity){
    		   io_printf(IO_BUF, "Random window generation enabled in timing_apply_post_spike\n");
    	   }
       }

       if (print_plasticity){
           io_printf(IO_BUF, "Random number: %u\n", random);
       }

       uint16_t window_length;
       if      (syn_type == 0) window_length = post_exp_dist_lookup_excit[random];
       else if (syn_type == 1) window_length = post_exp_dist_lookup_excit2[random];
       else if (syn_type == 2) window_length = post_exp_dist_lookup_inhib[random];
       else                    window_length = post_exp_dist_lookup_inhib2[random];

       uint32_t this_window_close_time = last_post_time + window_length;

       // Check if this post-spike extends the open window:
       if (previous_state.longest_post_pre_window_closing_time < this_window_close_time) {
          previous_state.longest_post_pre_window_closing_time = this_window_close_time;
       }

    // Decay accum value so that long periods without spikes cause it to forget:
    uint32_t time_since_last_event = time - last_event_time;

    // Param accum_decay_per_ts is actually per 32 time steps now, to avoid rounding to zero errors:
    int32_t acc_change = (recurrent_plasticity_params.accum_decay_per_ts * time_since_last_event>>5);


    // Decay pot_accumulator - THIS COULD BE WRONG TO DO HERE....
    previous_state.pot_accumulator -= acc_change;
    if (previous_state.pot_accumulator < 0) {
        previous_state.pot_accumulator = 0;
    }

    // Decay dep_accumulator
    previous_state.dep_accumulator += acc_change;
    if (previous_state.dep_accumulator > 0) {
    	previous_state.dep_accumulator = 0;
    }

    // Check if there was a post window open when this pre arrived and if so,
    // trigger an accum decrement (a step towards synaptic depression):
    if ((time > last_post_time) && (time < previous_state.longest_post_pre_window_closing_time)) {
        if (print_plasticity){
            io_printf(IO_BUF, "                                Pre spike has occurred inside a post window!\n");
            io_printf(IO_BUF, "                                longest post window closing time: %u \n", previous_state.longest_post_pre_window_closing_time);
        }
        // The pre-spike has occurred inside a post window.
        // Get time of event relative to last post-synaptic event
        uint32_t time_since_last_post = time - last_post_time;
        //io_printf(IO_BUF, "Dep time: %d was: %d\n", time, previous_state.dep_accumulator);

        if (previous_state.dep_accumulator >
            recurrent_plasticity_params.accum_dep_plus_one[syn_type]<<ACCUM_SCALING){
            // If accumulator's not going to hit depression limit, decrement it
            if (print_plasticity){ io_printf(IO_BUF, "        Decrementing Accumulator from: %d", previous_state.dep_accumulator); }
            previous_state.dep_accumulator = previous_state.dep_accumulator - (1<<ACCUM_SCALING);
            if (print_plasticity){ io_printf(IO_BUF, " to %d \n", previous_state.dep_accumulator); }

        } else  {
            //rndCountDep++;
            //if ((mars_kiss64_seed(recurrentSeed) & ((STDP_FIXED_POINT_ONE>>2) - 1))< (uint32_t)150){ // SD 110221 add stochasticity
            //rndYesCountDep++;
            //io_printf(IO_BUF, "Dep: Y: %u from %u\n", rndCountDep, rndYesCountDep);
            // We are hitting the depression threshold, so take action.
                // io_printf(IO_BUF, "DEP: t: %d, Vdiff: %k, histPot: %k    ", time, voltage_difference, post_synaptic_mem_V);
        	if (print_plasticity){ io_printf(IO_BUF, "        Accumulator limit reached: Depressing diff %k\n", voltage_difference); }
                if (previous_state.lock == 0){
                    // 24/5/21: SD Adding special case for inhib synapse, perform anti-Hebb learning, irrespective of voltage:
                    if (syn_type == 2) {  // Inhib synapse perform anti-Hebbian potentiation
	            	previous_state.lock = 1;
		     	previous_state.dep_accumulator = 0;
                        if (post_synaptic_neuron->V_membrane == 0.0k) { // Still in refrac. Allowed to potentiate this inhib synapse:
				previous_state.weight_state.weight = previous_state.weight_state.weight_region->max_weight;
				//previous_state.weight_state = weight_one_term_apply_potentiation_sd( previous_state.weight_state, syn_type, STDP_FIXED_POINT_ONE);
                        } 
                    } // End of if syn_type == 2....
                    //io_printf(IO_BUF, "Thresh: %k, v: %k\n", post_synaptic_threshold->threshold_value, post_synaptic_mem_V);
                    // SD 9/2/21: Reverse order of these conditions: 
                    else if ((voltage_difference > v_diff_pot_threshold) && (voltage_difference < 900.0k)) {
                        // Neuron fired by teacher and is far away from firing by FF alone.
                        // This synapse is probably in the post window. Full depress.
			previous_state.lock = 1;
			previous_state.dep_accumulator = 0;
			previous_state.weight_state = weight_one_term_apply_depression_sd( previous_state.weight_state, syn_type, STDP_FIXED_POINT_ONE);
			if (print_plasticity) { io_printf(IO_BUF, "            Applying full depression (gap to threshold: %k)\n", voltage_difference); }
                        
                    } else{
                        // Neuron is firing slightly too early or by teacher. No major adjustment here.
                        // SD 19/5/21: Reduce synapse values to two (pot and dep) by eliminating neutral value.
	            	previous_state.lock = 1;
		     	previous_state.dep_accumulator = 0;
                       if (!locked_weights_unchanged) {
                           // 8/6/21: SD Put back lock at baseline
                            previous_state.weight_state.weight = previous_state.weight_state.weight + inc_LL_dep;
			   //previous_state.weight_state = weight_one_term_apply_depression_sd( previous_state.weight_state, syn_type, STDP_FIXED_POINT_ONE);
                           //previous_state.weight_state.weight = previous_state.weight_state.weight - inc_LL_dep;
                       }
                    }
                    /* SD 9/2/21: Reverse ordering of conditions.
                    if ((voltage_difference < v_diff_pot_threshold) || (voltage_difference > 900.0k)) {
                        // Either voltage near thresh when teacher arrived, or neuron fired based on FF alone.
                        // Near perfect balance. Don't depress this synapse significantly:
                        //io_printf(IO_BUF, "%d : LL dep - near balance\n", time);
	            	previous_state.lock = 1;
		     	previous_state.dep_accumulator = 0;
                       if (!locked_weights_unchanged) {
                           previous_state.weight_state.weight = previous_state.weight_state.weight + inc_LL_dep;
                       }
                    } else {
                        // Neuron fires by feedforward input alone. Probably firing too early. 
                        // Enable full depression, which should push the firing a bit later.
                        //io_printf(IO_BUF, "%d : Full dep\n", time);
			previous_state.lock = 1;
			previous_state.dep_accumulator = 0;
			previous_state.weight_state = weight_one_term_apply_depression_sd( previous_state.weight_state, syn_type, STDP_FIXED_POINT_ONE);
			if (print_plasticity) { io_printf(IO_BUF, "            Applying full depression (gap to threshold: %k)\n", voltage_difference); }
                    } */ 
                } // previous_state.lock == 0
                else {
                    //io_printf(IO_BUF, "%d : Dep LOCKED\n", time);
                    if (print_plasticity){ io_printf(IO_BUF, "Synapse already locked, so cannot depress\n"); }
                } // previous_state==lock, else

        } // previous_state.dep_accumulator >..., else clause
    }  // ((time > last_post_time) && ....
    else { if (print_plasticity){ io_printf (IO_BUF, "        PRE SPIKE WAS NOT IN POST WINDOW!!\n"); } }

    // Set the post window to be just before this pre-spike. This is the only way I've found to
    // reset it. It means that the first window length will be garbage.
    previous_state.longest_post_pre_window_closing_time = time - 1;
    previous_state.pre_waiting_post = true;

    return previous_state;
}

// This routine has different functionality depending on synapse type.
// It has two major responsibilities:
// 1) Generate the window size for this post spike and extend the window closure time
//    if this is beyond the current value. This is used by a following pre-spike for depression
// 2) Check if there is currently a pre-window open and then check if the post-spike is within
//    it. If so:
//               a) increment the accumulator
//               b) perform potentiation and reset accumulator if it has reached threshold
//               c) set the pre_found_post flag, equivalent to clearing the pre_waiting_post
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
   // Also extract flag indicating whether neuron was fired by presynaptic input (not Teacher!)
   accum voltage_difference;

   if (post_synaptic_mem_V > 900.0k) {
	   // neuron was fired by presynaptic input
	   voltage_difference = 1000.0k;
   } else {
	   // neuron was fired by Teacher
	   voltage_difference = post_synaptic_threshold->threshold_value - post_synaptic_mem_V;
   }

   // Voltage difference will be rectified (so no negative values allowed):
   if (voltage_difference < (accum) 0.0) {
      voltage_difference = (accum) 0.0;
   }

   //log_info("Thr: %k, postV: %k", post_synaptic_threshold->threshold_value, post_synaptic_mem_V);
   // log_info("Post_synaptic_potential from within apply post spike: %k", post_synaptic_mem_V);

   // Get time of event relative to last pre-synaptic event
   uint32_t time_since_last_pre = time - last_pre_time;

   // If spikes don't coincide:
   if (previous_state.pre_waiting_post == true && time_since_last_pre > 0) {
       previous_state.pre_waiting_post = false;

       // Now check if this post spike occurred in the open window created by the previous pre-spike  :
       //Qif (time_since_last_pre <= my_last_pre_trace) {  // SD 16/6/20: Generate window length for each connection instead of sharing
       if (time_since_last_pre <= last_pre_trace) {
           //io_printf(IO_BUF, "Pot time: %d was: %d\n", time, previous_state.pot_accumulator);

           if (previous_state.pot_accumulator < recurrent_plasticity_params.accum_pot_minus_one[syn_type]<<ACCUM_SCALING){
               // If accumulator's not going to hit potentiation limit, increment it:

               previous_state.pot_accumulator = previous_state.pot_accumulator + (1<<ACCUM_SCALING);
               if (print_plasticity){ io_printf(IO_BUF, "        Incrementing Accumulator to: %u\n", previous_state.pot_accumulator); }
           } else {
               //rndCountPot++;
               //if ((mars_kiss64_seed(recurrentSeed) & ((STDP_FIXED_POINT_ONE>>2) - 1))< (uint32_t)150){ // SD 110221 add stochasticity
               //rndYesCountPot++;
               //io_printf(IO_BUF, "Pot: Y: %u from %u\n", rndCountDep, rndYesCountDep);
               if (print_plasticity){ io_printf(IO_BUF, "        ACCUMULATOR Hit Threshold, entering weight update for synapse of type: %u, lock state: %u \n", syn_type, previous_state.lock); }

               //io_printf(IO_BUF, "POT: t: %d, Vdiff: %k, histSomaPot: %k    ", time, voltage_difference, post_synaptic_mem_V);
               if (print_plasticity){ io_printf(IO_BUF, "Updating Type: 0 Synapse\n"); }
               // Check synapse is unlocked
               if (previous_state.lock == 0) {
                   //io_printf(IO_BUF, "Thresh: %k, v: %k\n", post_synaptic_threshold->threshold_value, post_synaptic_mem_V);
                   if (syn_type == 2) { // For inhibitory synapses do nothing but lock the synapse and reset accumulator:
                       previous_state.lock = 1;
                       previous_state.pot_accumulator = 0;
                   }
                   else if (voltage_difference > 900.0k) {
                       // Neuron fired through feed-forward input, ahead of desired time. Therefore, depress!! (New functionality!)
                       if (print_plasticity){ io_printf(IO_BUF, "was FF pot\n"); }
                       //io_printf(IO_BUF, "%d : pot syn - dep tuning\n", time);
                       previous_state.lock = 1;
                       previous_state.pot_accumulator = 0;
			previous_state.weight_state = weight_one_term_apply_depression_sd( previous_state.weight_state, syn_type, STDP_FIXED_POINT_ONE);
                       if (!locked_weights_unchanged) {
                        previous_state.weight_state.weight = previous_state.weight_state.weight + inc_tune_dep;
                       }
                   } else if (voltage_difference > v_diff_pot_threshold) {
                       // Neuron fired through teacher but still far from threshold using FF alone
                       //io_printf(IO_BUF, "%d : pot syn - big potentiation\n", time);
                       previous_state.weight_state = weight_one_term_apply_potentiation_sd( previous_state.weight_state, syn_type, STDP_FIXED_POINT_ONE);
                       previous_state.lock = 1;
                       previous_state.pot_accumulator = 0;
                   } // if voltage_difference < v_diff_pot_threshold
                   else {
                       // Teacher triggers neuron to fire. Therefore we need full potentiation to make spike happen by FF input:
                       previous_state.lock = 1;
                       previous_state.pot_accumulator = 0;
                       // SD 19/02/21: When nearly able to fire by FF alone, do a locked low, so that spike is kept a bit late, but 
                       //              does not jump to be much earlier. (Comment out potentiation and do a LL-pot:
                       //SD 250821 - remove this: previous_state.weight_state = weight_one_term_apply_potentiation_sd( previous_state.weight_state, syn_type, STDP_FIXED_POINT_ONE);
                       if (!locked_weights_unchanged) {
                           previous_state.weight_state.weight = previous_state.weight_state.weight + inc_tune_pot;
                       }
                       //io_printf(IO_BUF, "%d : pot syn - pot tuning\n", time);
                       if (print_plasticity){
               	           io_printf(IO_BUF, "Voltage  diff: %k, so potentiate\n", voltage_difference);
                           io_printf(IO_BUF, "Old weight: %u, ", previous_state.weight_state);
                           io_printf(IO_BUF, "New Weight: %u \n", previous_state.weight_state);
                       }
                   } // if voltage_diff > 900.0k ... else
               } else { // previous_state.locked == 0, else
                   //io_printf(IO_BUF, "%d : Pot LOCKED\n", time);
                   if (print_plasticity){ io_printf(IO_BUF, "Synapse is already locked\n"); }
               } // if prev_state.lock == 0, else clause
           // Used for stochasticity} // if prev_state.pot_acc  thresh, else clause
         } // SD else
       } // if time_since_last_pre <= last_pre_trace
   }  // if previous_state.pre_waiting_post == true....

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

   uint16_t shift_to_print = 15 - state.weight_multiply_right_shift - global_weight_scale;

   //io_printf(IO_BUF, "    Fixed Initial weight: %k, max_weight: %k\n",
//		   state.weight << shift_to_print, state.weight_region->max_weight << shift_to_print);
 //  io_printf(IO_BUF, "    Int   Initial weight: %u, max_weight: %u\n",
//		   state.weight, state.weight_region->max_weight);

   int32_t scale = maths_fixed_mul16(
                   state.weight_region->max_weight - state.weight,
                   state.weight_region->a2_plus, (state.weight_multiply_right_shift + global_weight_scale));

   //io_printf(IO_BUF, "        A+: %u", state.weight_region->a2_plus);
   //io_printf(IO_BUF, "        shift: %u \n", state.weight_multiply_right_shift);

   //io_printf(IO_BUF, "        scale: %u, potentiation: %k \n", scale , potentiation << 4);

   state.weight += (scale);


   //io_printf(IO_BUF, "    Fixed Updated weight: %k, max weight: %k\n",
   //		   state.weight << shift_to_print, state.weight_region->max_weight << shift_to_print);
   //io_printf(IO_BUF, "    Int   Updated weight: %u, max weight: %u\n",
   //		   state.weight, state.weight_region->max_weight);
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

   uint16_t shift_to_print = 15 - state.weight_multiply_right_shift - global_weight_scale;

   //io_printf(IO_BUF, "    Fixed Initial weight: %k, min_weight: %k\n",
   //		   state.weight << shift_to_print, state.weight_region->min_weight << shift_to_print);

   //io_printf(IO_BUF, "    Int   Initial weight: %u, min_weight: %u\n",
   //		   state.weight, state.weight_region->min_weight);

   int32_t scale = maths_fixed_mul16(
                   state.weight - state.weight_region->min_weight,
                   state.weight_region->a2_minus, (state.weight_multiply_right_shift + global_weight_scale));

   //io_printf(IO_BUF, "        A-: %u", state.weight_region->a2_minus);
   //io_printf(IO_BUF, "        shift: %u \n", state.weight_multiply_right_shift);

   //io_printf(IO_BUF, "        scale: %u, depression: %k \n", scale , depression << 4);

   state.weight -= (scale);


   //io_printf(IO_BUF, "    Fixed Updated weight: %k, max weight: %k\n",
   //		   state.weight << shift_to_print, state.weight_region->max_weight << shift_to_print);
   //io_printf(IO_BUF, "    Int   Updated weight: %u, max weight: %u\n",
   //		   state.weight, state.weight_region->max_weight);



   return state;
}

#endif  // _TIMING_RECURRENT_CYCLIC_IMPL_H_
