// Spinn_common includes
#include "static-assert.h"

// sPyNNaker neural modelling includes
#include "../../synapses.h"

// Plasticity common includes
#include "../common/maths.h"
#include "../common/post_events.h"

#include "weight_dependence/weight.h"
#include "timing_dependence/timing.h"
#include <string.h>
#include <debug.h>

uint32_t num_plastic_pre_synaptic_events = 0;

//---------------------------------------
// Macros
//---------------------------------------
// The plastic control words used by Morrison synapses store an axonal delay in the upper 3 bits
// Assuming a maximum of 16 delay slots, this is all that is required as:
//
// 1) Dendritic + Axonal <= 15
// 2) Dendritic >= Axonal
//
// Therefore:
//
// * Maximum value of dendritic delay is 15 (with axonal delay of 0) - It requires 4 bits
// * Maximum value of axonal delay is 7 (with dendritic delay of 8) - It requires 3 bits
//
//             |        Axonal delay       |  Dendritic delay   |       Type        |      Index         |
//             |---------------------------|--------------------|-------------------|--------------------|
// Bit count   | SYNAPSE_AXONAL_DELAY_BITS | SYNAPSE_DELAY_BITS | SYNAPSE_TYPE_BITS | SYNAPSE_INDEX_BITS |
//             |                           |                    |        SYNAPSE_TYPE_INDEX_BITS         |
//             |---------------------------|--------------------|----------------------------------------|
#ifndef SYNAPSE_AXONAL_DELAY_BITS
  #define SYNAPSE_AXONAL_DELAY_BITS 3
#endif

#define SYNAPSE_AXONAL_DELAY_MASK ((1 << SYNAPSE_AXONAL_DELAY_BITS) - 1)

#define SYNAPSE_DELAY_TYPE_INDEX_BITS \
    (SYNAPSE_DELAY_BITS + SYNAPSE_TYPE_INDEX_BITS)

#if (SYNAPSE_DELAY_TYPE_INDEX_BITS + SYNAPSE_AXONAL_DELAY_BITS) > 16
  #error "Not enough bits for axonal synaptic delay bits"
#endif

//---------------------------------------
// Structures
//---------------------------------------
typedef struct
{
  pre_trace_t prev_trace;
  uint32_t prev_time;
} pre_event_history_t;

post_event_history_t *post_event_history;
uint32_t weight_update_constant_component;
uint32_t last_dopamine_spike_time = 0;
weight_state_t weight_state;


//---------------------------------------
// Dopamine trace is a simple decaying trace similarly implemented as pre and
// post trace.
static inline post_trace_t add_dopamine_spike(
        uint32_t time, int16_t concentration, int16_t* last_dopamine_level) {

    // Get time since last dopamine spike
    uint32_t delta_time = time - last_dopamine_spike_time;

    // Apply exponential decay to get the current value
    int32_t decayed_trace = STDP_FIXED_MUL_16X16(*last_dopamine_level,
            DECAY_LOOKUP_TAU_D(delta_time));

    // Increase dopamine level due to new spike
    int16_t new_trace = decayed_trace + concentration;

    last_dopamine_spike_time = time;
    *last_dopamine_level = new_trace;

    // Return decayed dopamine trace
    return (post_trace_t) { .stdp_post_trace = 0, .dopamine = new_trace };
}

static inline void correlation_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, uint32_t last_non_dopamine_spike_time,
        uint32_t last_update_time, plastic_synapse_t *previous_state,
        post_event_history_t *post_event_history) {

    use(&trace);

    // Calculate EXP components in JK's weight update equation
    int16_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
        time - last_non_dopamine_spike_time);
    int16_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
        time - post_event_history -> last_dopamine_spike_time);
    int16_t third_exp_component;
    if (last_update_time == last_non_dopamine_spike_time)
        third_exp_component = DECAY_LOOKUP_TAU_D(
            last_non_dopamine_spike_time -
            post_event_history -> last_dopamine_spike_time);
    else
        third_exp_component = DECAY_LOOKUP_TAU_C(
             post_event_history -> last_dopamine_spike_time -
             last_non_dopamine_spike_time);

    // Evaluate weight function
    uint32_t weight_change = STDP_FIXED_MUL_16X16(
            STDP_FIXED_MUL_16X16(post_event_history -> last_neuromodulator_trace,
                previous_state -> eligibility_trace),
            STDP_FIXED_MUL_16X16(weight_update_constant_component,
        STDP_FIXED_MUL_16X16(decay_eligibility_trace, decay_dopamine_trace)
            - third_exp_component));

    previous_state -> weight += weight_change;

    // Saturate weight
    previous_state -> weight= MIN(weight_state.weight_region->max_weight,
                                  MAX(previous_state -> weight,
                                  weight_state.weight_region->min_weight));

    // Update eligibility trace if this spike is non-dopamine spike
    if (trace.dopamine == 0) {
        // Decay eligibility trace
        int32_t decayed_eligibility_trace = STDP_FIXED_MUL_16X16(
            previous_state -> eligibility_trace, decay_eligibility_trace);

        // Apply STDP
        uint32_t time_since_last_pre = time - last_pre_time;
        if (time_since_last_pre > 0) {
            int32_t decayed_r1 = STDP_FIXED_MUL_16X16(
                last_pre_trace, DECAY_LOOKUP_TAU_PLUS(time_since_last_pre));
            decayed_eligibility_trace += decayed_r1;
        }
        previous_state -> eligibility_trace = decayed_eligibility_trace;
    }
}

static inline void correlation_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_post_time,
        post_trace_t last_post_trace, uint32_t last_non_dopamine_spike_time,
        uint32_t last_update_time, plastic_synapse_t *previous_state,
        post_event_history_t *post_event_history) {

    use(&trace);
    use(&last_post_trace);

    // Calculate EXP components in JK's weight update equation
    int16_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
        time - last_non_dopamine_spike_time);
    int16_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
        time - post_event_history -> last_dopamine_spike_time);
    int16_t third_exp_component;
    if (last_update_time == last_non_dopamine_spike_time)
        third_exp_component = DECAY_LOOKUP_TAU_D(
            last_non_dopamine_spike_time -
            post_event_history -> last_dopamine_spike_time);
    else
        third_exp_component = DECAY_LOOKUP_TAU_C(
             post_event_history -> last_dopamine_spike_time -
             last_non_dopamine_spike_time);

    // Evaluate weight function
    uint32_t weight_change = STDP_FIXED_MUL_16X16(
            STDP_FIXED_MUL_16X16(post_event_history -> last_neuromodulator_trace,
                previous_state -> eligibility_trace),
            STDP_FIXED_MUL_16X16(weight_update_constant_component,
        STDP_FIXED_MUL_16X16(decay_eligibility_trace, decay_dopamine_trace)
            - third_exp_component));

    previous_state -> weight += weight_change;

    if (previous_state -> weight & 0x8000)
        previous_state -> weight = 0;
    else
        // Saturate weight
        previous_state -> weight= MIN(weight_state.weight_region->max_weight,
                                      MAX(previous_state -> weight,
                                      weight_state.weight_region->min_weight));

    // Update eligibility trace if this spike is non-dopamine spike
    if (last_post_trace.dopamine == 0) {
        // Decay eligibility trace
        int32_t decayed_eligibility_trace = STDP_FIXED_MUL_16X16(
            previous_state -> eligibility_trace, decay_eligibility_trace);

        // Apply STDP
        uint32_t time_since_last_post = time - last_post_time;
        if (time_since_last_post > 0) {
            int32_t decayed_r1 = STDP_FIXED_MUL_16X16(
                last_post_trace.stdp_post_trace,
                DECAY_LOOKUP_TAU_MINUS(time_since_last_post));
            decayed_eligibility_trace -= decayed_r1;
            if (decayed_eligibility_trace < 0) decayed_eligibility_trace = 0;
        }
        previous_state -> eligibility_trace = decayed_eligibility_trace;
    }
}

// Synapse update loop
//---------------------------------------
static inline plastic_synapse_t plasticity_update_synapse(
    uint32_t time,
    const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
    const pre_trace_t new_pre_trace, const uint32_t delay_dendritic,
    const uint32_t delay_axonal, plastic_synapse_t *current_state,
    post_event_history_t *post_event_history) {

    // Apply axonal delay to time of last presynaptic spike
    const uint32_t delayed_last_pre_time = last_pre_time + delay_axonal;

    // Get the post-synaptic window of events to be processed
    const uint32_t window_begin_time = (delayed_last_pre_time >= delay_dendritic) ?
        (delayed_last_pre_time - delay_dendritic) : 0;
    const uint32_t window_end_time = time + delay_axonal - delay_dendritic;
    post_event_window_t post_window = post_events_get_window_delayed(
        post_event_history, window_begin_time, window_end_time);

    // Process events in post-synaptic window
    uint32_t prev_corr_time = delayed_last_pre_time;
    uint32_t last_non_dopamine_spike_time = delayed_last_pre_time;

    while(post_window.num_events > 0) {
        const uint32_t delayed_post_time =
            *post_window.next_time + delay_dendritic;

        correlation_apply_post_spike(
            delayed_post_time, *post_window.next_trace,
            delayed_last_pre_time, last_pre_trace,
            last_non_dopamine_spike_time, prev_corr_time,
            current_state, post_event_history);

        // Update previous correlation to point to this post-event
        prev_corr_time = delayed_post_time;

        // Update previous traces and times
        if (post_window.next_trace -> dopamine == 0) {
            last_non_dopamine_spike_time = delayed_post_time;
        }
        else {
            post_event_history -> last_neuromodulator_trace =
                post_window.next_trace -> dopamine;
            post_event_history -> last_dopamine_spike_time = delayed_post_time;
        }

        // Go onto next event
        post_window = post_events_next_delayed(post_window, delayed_post_time);
    }

    const uint32_t delayed_pre_time = time + delay_axonal;

    correlation_apply_pre_spike(
        delayed_pre_time, new_pre_trace,
        post_window.prev_time, post_window.prev_trace,
        last_non_dopamine_spike_time, prev_corr_time,
        current_state, post_event_history);

    return *current_state;
}

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    // Load timing dependence data
    address_t weight_region_address = timing_initialise(address);
    if (address == NULL) {
        return false;
    }

    // Read Izhikevich weight update equation constant component
    weight_update_constant_component = *weight_region_address++;

    // Load weight dependence data
    address_t weight_result = weight_initialise(
        weight_region_address, ring_buffer_to_input_buffer_left_shifts);
    if (weight_result == NULL) {
        return false;
    }

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        return false;
    }

    return true;
}

//---------------------------------------
// Synaptic row plastic-region implementation
//---------------------------------------
static inline plastic_synapse_t* plastic_synapses(address_t plastic) {
    const uint32_t pre_event_history_size_words =
        sizeof(pre_event_history_t) / sizeof(uint32_t);
    static_assert(pre_event_history_size_words * sizeof(uint32_t) == sizeof(pre_event_history_t),
        "Size of pre_event_history_t structure should be a multiple of 32-bit words");

    return (plastic_synapse_t*)(&plastic[pre_event_history_size_words]);
}

//---------------------------------------
static inline pre_event_history_t *plastic_event_history(address_t plastic) {
    return (pre_event_history_t*)(&plastic[0]);
}

//---------------------------------------
static inline index_t sparse_axonal_delay(uint32_t x) {
    return ((x >> SYNAPSE_DELAY_TYPE_INDEX_BITS) & SYNAPSE_AXONAL_DELAY_MASK);
}

//---------------------------------------
void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    log_debug("Adding post-synaptic event to trace at time:%u", time);

    // Add post-event
    post_event_history_t *history = &post_event_history[neuron_index];
    const uint32_t last_post_time = history->times[history->count_minus_one];
    const post_trace_t last_post_trace =
        history->traces[history->count_minus_one];
    post_events_add(time, history, timing_add_post_spike(time, last_post_time,
                                                         last_post_trace));
}

//--------------------------------------
void synapse_dynamics_process_neuromodulator_event(
        uint32_t time, int16_t concentration, uint32_t neuron_index) {
    log_debug("Adding neuromodulation event to trace at time:%u concentration: %d", time, concentration);

    // Get post event history of this neuron
    post_event_history_t *history = &post_event_history[neuron_index];

    // Update neuromodulator level reaching this post synaptic neuron
    post_events_add(time, history, add_dopamine_spike(time,
        concentration, &(history -> neuromodulator_level)));
}

//---------------------------------------
void synapse_dynamics_process_plastic_synapses(address_t plastic,
         address_t fixed, weight_t *ring_buffer, uint32_t time) {

    // Extract seperate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    plastic_synapse_t *plastic_words = plastic_synapses(plastic);
    const control_t *control_words = synapse_row_plastic_controls(fixed);
    size_t plastic_synapse  = synapse_row_num_plastic_controls(fixed);

    num_plastic_pre_synaptic_events += plastic_synapse;

    // Get event history from synaptic row
    pre_event_history_t *event_history = plastic_event_history(plastic);

    // Get last pre-synaptic event from event history
    const uint32_t last_pre_time = event_history->prev_time;
    const pre_trace_t last_pre_trace = event_history->prev_trace;

    // Update pre-synaptic trace
    log_debug("Adding pre-synaptic event to trace at time:%u", time);
    event_history->prev_time = time;
    event_history->prev_trace = timing_add_pre_spike(time, last_pre_time,
                                                     last_pre_trace);

    // Loop through plastic synapses
    for ( ; plastic_synapse > 0; plastic_synapse--)
    {
        // Get next control word (autoincrementing)
        uint32_t control_word = *control_words++;

        // Extract control-word components
        // **NOTE** cunningly, control word is just the same as lower
        // 16-bits of 32-bit fixed synapse so same functions can be used
        uint32_t delay_dendritic = synapse_row_sparse_delay(control_word);
        uint32_t delay_axonal = 0;//sparse_axonal_delay(control_word);
        uint32_t type_index = synapse_row_sparse_type_index(control_word);

        // Convert into ring buffer offset
        uint32_t offset = synapses_get_ring_buffer_index_combined(
            delay_axonal + delay_dendritic + time, type_index);

        uint32_t type = synapse_row_sparse_type(control_word);
        uint32_t index = synapse_row_sparse_index(control_word);

       // Get state of synapse - weight and eligibility trace.
       plastic_synapse_t* current_state = plastic_words;
       weight_state = weight_get_initial(current_state -> weight, type);
       log_debug("Synapse state %x, weight %f", *current_state, current_state -> weight);
       log_debug("Eligibility trace %f", current_state -> eligibility_trace);

       // Update the synapse state
       plastic_synapse_t final_state = plasticity_update_synapse(time,
           last_pre_time, last_pre_trace,
           event_history->prev_trace, delay_dendritic, delay_axonal,
           current_state, &post_event_history[index]);

       // Add weight to ring-buffer entry
       ring_buffer[offset] += final_state.weight;

       // Write back updated synaptic word to plastic region
       *plastic_words++ = final_state;
    }
    return true;
}

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(){
    return num_plastic_pre_synaptic_events;
}


input_t synapse_dynamics_get_intrinsic_bias(uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
    return 0.0k;
}

//---------------------------------------
#ifdef DEBUG
void print_plastic_synapses(address_t plastic, address_t fixed)
{
  // Extract seperate arrays of weights (from plastic region),
  // Control words (from fixed region) and number of plastic synapses
  /*const weight_t *weights = plastic_weights(plastic);
  const control_t *control_words = plastic_controls(fixed);
  size_t plastic_synapse  = num_plastic_controls(fixed);
  const pre_synaptic_event_history_t *event_history = plastic_event_history(plastic);

  printf ("Plastic region %u synapses pre-synaptic event buffer count:%u:\n", plastic_synapse, event_history->count);

  // Loop through plastic synapses
  for (uint32_t i = 0; i < plastic_synapse; i++)
  {
    // Get next weight and control word (autoincrementing control word)
    uint32_t weight = *weights++;
    uint32_t control_word = *control_words++;

    printf ("%08x [%3d: (w: %5u (=", control_word, i, weight);
    print_weight (weight);
    printf ("pA) d: %2u, %c, n = %3u)] - {%08x %08x}\n",
      sparse_delay(control_word),
      (sparse_type(control_word)==0)? 'X': 'I',
      sparse_index(control_word),
      SYNAPSE_DELAY_MASK,
      SYNAPSE_TYPE_INDEX_BITS
    );
  }*/
}
#endif  // DEBUG
