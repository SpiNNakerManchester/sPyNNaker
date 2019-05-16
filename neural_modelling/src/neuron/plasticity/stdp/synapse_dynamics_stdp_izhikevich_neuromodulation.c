// Spinn_common includes
#include "static-assert.h"

// sPyNNaker neural modelling includes
#include <neuron/synapses.h>

// Plasticity common includes
#include "maths.h"
#include "post_events_with_da.h"

#include "weight_dependence/weight.h"
#include "timing_dependence/timing.h"
#include <debug.h>
#include <utils.h>
#include <neuron/plasticity/synapse_dynamics.h>

static uint32_t synapse_type_index_bits;
static uint32_t synapse_index_bits;
static uint32_t synapse_index_mask;
static uint32_t synapse_type_index_mask;
static uint32_t synapse_delay_index_type_bits;
static uint32_t synapse_type_mask;

uint32_t num_plastic_pre_synaptic_events = 0;
uint32_t plastic_saturation_count = 0;

//---------------------------------------
// Macros
//---------------------------------------
// The plastic control words used by Morrison synapses store an axonal delay
// in the upper 3 bits.
// Assuming a maximum of 16 delay slots, this is all that is required as:
//
// 1) Dendritic + Axonal <= 15
// 2) Dendritic >= Axonal
//
// Therefore:
//
// * Maximum value of dendritic delay is 15 (with axonal delay of 0)
//    - It requires 4 bits
// * Maximum value of axonal delay is 7 (with dendritic delay of 8)
//    - It requires 3 bits
//
// |        Axonal delay       |  Dendritic delay   |       Type        |      Index         |
// |---------------------------|--------------------|-------------------|--------------------|
// | SYNAPSE_AXONAL_DELAY_BITS | SYNAPSE_DELAY_BITS | SYNAPSE_TYPE_BITS | SYNAPSE_INDEX_BITS |
// |                           |                    |        SYNAPSE_TYPE_INDEX_BITS         |
// |---------------------------|--------------------|----------------------------------------|

#ifndef SYNAPSE_AXONAL_DELAY_BITS
#define SYNAPSE_AXONAL_DELAY_BITS 3
#endif

#define SYNAPSE_AXONAL_DELAY_MASK ((1 << SYNAPSE_AXONAL_DELAY_BITS) - 1)

#define SMULBB_STDP_FIXED(a, b) (__smulbb(a, b) >> STDP_FIXED_POINT)

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
  pre_trace_t prev_trace;
  uint32_t prev_time;
} pre_event_history_t;

post_event_history_t *post_event_history;
uint32_t weight_update_constant_component;
weight_state_t weight_state;

//---------------------------------------
// On each dopamine spike arrival, we add a new history trace in the post
// synaptic history trace buffer
static inline post_trace_t add_dopamine_spike(
        uint32_t time, int32_t concentration, uint32_t last_post_time,
        post_trace_t last_trace, uint32_t synapse_type) {

    // Get time since last dopamine spike
    uint32_t delta_time = time - last_post_time;

    // Apply exponential decay to get the current value of the dopamine
    // trace
    int32_t decayed_dopamine_trace = __smulbb(last_trace,
            DECAY_LOOKUP_TAU_D(delta_time)) >> STDP_FIXED_POINT;

    // Put dopamine concentration into STDP fixed-point format
    weight_state_t weight_state = weight_get_initial(
        concentration, synapse_type);
    if (weight_state.weight_multiply_right_shift > STDP_FIXED_POINT) {
        concentration >>=
           (weight_state.weight_multiply_right_shift - STDP_FIXED_POINT);
    }
    else {
        concentration <<=
           (STDP_FIXED_POINT - weight_state.weight_multiply_right_shift);
    }

    // Step increase dopamine trace due to new spike
    int32_t new_dopamine_trace = decayed_dopamine_trace + concentration;

    // Decay previous post trace
    int32_t decayed_last_post_trace = __smultb(
            last_trace,
            DECAY_LOOKUP_TAU_MINUS(delta_time)) >> STDP_FIXED_POINT;

    return (post_trace_t) trace_build(decayed_last_post_trace,
        new_dopamine_trace);
}

static inline void correlation_apply_post_spike(
        uint32_t time, post_trace_t trace, uint32_t last_pre_time,
        pre_trace_t last_pre_trace, int32_t last_dopamine_trace,
        uint32_t last_update_time, plastic_synapse_t *previous_state,
        bool dopamine, int32_t* weight_update) {

    use(&trace);

    // Calculate EXP components of the weight update equation
    int32_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
        time - last_update_time);
    int32_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
        time - last_update_time);

    if (last_dopamine_trace != 0) {
        // Evaluate weight function
        uint32_t temp = SMULBB_STDP_FIXED(
            SMULBB_STDP_FIXED(last_dopamine_trace, *previous_state),
            SMULBB_STDP_FIXED(
                decay_eligibility_trace, decay_dopamine_trace)
                 - STDP_FIXED_POINT_ONE);

        *weight_update += maths_fixed_mul32(weight_update_constant_component,
                                                   temp, STDP_FIXED_POINT);
    }

    int32_t decayed_eligibility_trace = __smulbb(
        *previous_state, decay_eligibility_trace) >> STDP_FIXED_POINT;

    // Apply STDP to the eligibility trace if this spike is non-dopamine spike
    if (!dopamine) {
        // Apply STDP
        uint32_t time_since_last_pre = time - last_pre_time;
        if (time_since_last_pre > 0) {
            int32_t decayed_pre_trace = __smulbb(
                last_pre_trace, DECAY_LOOKUP_TAU_PLUS(time_since_last_pre)) >> STDP_FIXED_POINT;
            decayed_pre_trace = __smulbb(decayed_pre_trace,
                weight_state.weight_region -> a2_plus) >> weight_state.weight_multiply_right_shift;
            decayed_eligibility_trace += decayed_pre_trace;
        }
    }

    // Update eligibility trace in synapse state
    *previous_state =
        synapse_structure_update_state(decayed_eligibility_trace,
            synapse_structure_get_weight(*previous_state));
}

static inline void correlation_apply_pre_spike(
        uint32_t time, pre_trace_t trace, uint32_t last_post_time,
        post_trace_t last_post_trace, int32_t last_dopamine_trace,
        plastic_synapse_t *previous_state, bool dopamine,
        int32_t* weight_update) {

    use(&trace);
    use(&last_post_trace);

    // Calculate EXP components of the weight update equation
    int32_t decay_eligibility_trace = DECAY_LOOKUP_TAU_C(
        time - last_post_time);
    int32_t decay_dopamine_trace = DECAY_LOOKUP_TAU_D(
        time - last_post_time);

    if (last_dopamine_trace != 0) {
        // Evaluate weight function
        uint32_t temp = SMULBB_STDP_FIXED(
            SMULBB_STDP_FIXED(last_dopamine_trace, *previous_state),
            SMULBB_STDP_FIXED(
                decay_eligibility_trace, decay_dopamine_trace)
                 - STDP_FIXED_POINT_ONE);

        *weight_update += maths_fixed_mul32(weight_update_constant_component,
                                                   temp, STDP_FIXED_POINT);
    }

    int32_t decayed_eligibility_trace = __smulbb(
        *previous_state, decay_eligibility_trace) >> STDP_FIXED_POINT;

    // Apply STDP to the eligibility trace if this spike is non-dopamine spike
    uint32_t time_since_last_post = time - last_post_time;
    if (time_since_last_post > 0) {
        int32_t decayed_post_trace = __smultb(
            last_post_trace,
            DECAY_LOOKUP_TAU_MINUS(time_since_last_post)) >> STDP_FIXED_POINT;
        decayed_post_trace = __smulbb(decayed_post_trace,
            weight_state.weight_region -> a2_minus) >> weight_state.weight_multiply_right_shift;
        decayed_eligibility_trace -= decayed_post_trace;
        if (decayed_eligibility_trace < 0) {
            decayed_eligibility_trace = 0;
        }
    }

    // Update eligibility trace in synapse state
    *previous_state =
        synapse_structure_update_state(decayed_eligibility_trace,
            synapse_structure_get_weight(*previous_state));
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

    uint32_t prev_corr_time = delayed_last_pre_time;
    int32_t last_dopamine_trace = __smulbb(post_window.prev_trace,
            DECAY_LOOKUP_TAU_D(delayed_last_pre_time - post_window.prev_time))
            >> STDP_FIXED_POINT;
    bool next_trace_is_dopamine = false;
    int32_t weight_update = 0;

    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time =
            *post_window.next_time + delay_dendritic;
        next_trace_is_dopamine = post_events_next_is_dopamine(post_window);

        correlation_apply_post_spike(
            delayed_post_time, *post_window.next_trace,
            delayed_last_pre_time, last_pre_trace,
            last_dopamine_trace,
            prev_corr_time, current_state,
            next_trace_is_dopamine,
            &weight_update);

        // Update previous correlation to point to this post-event
        prev_corr_time = delayed_post_time;
        last_dopamine_trace = get_dopamine_trace(*post_window.next_trace);

        // Go onto next event
        post_window = post_events_next_delayed(post_window, delayed_post_time);
    }

    const uint32_t delayed_pre_time = time + delay_axonal;

    correlation_apply_pre_spike(
        delayed_pre_time, new_pre_trace,
        prev_corr_time, post_window.prev_trace,
        last_dopamine_trace, current_state,
        next_trace_is_dopamine,
        &weight_update);

    // Put total weight change into correct run-time weight fixed-point format
    // NOTE: Accuracy loss when shifting right.
    if (weight_state.weight_multiply_right_shift > STDP_FIXED_POINT) {
        weight_update <<=
           (weight_state.weight_multiply_right_shift - STDP_FIXED_POINT);
    }
    else {
        weight_update >>=
           (STDP_FIXED_POINT - weight_state.weight_multiply_right_shift);
    }

    int32_t new_weight = weight_update + synapse_structure_get_weight(*current_state);

    // Saturate weight
    new_weight = MIN(weight_state.weight_region->max_weight,
                        MAX(new_weight,
                            weight_state.weight_region->min_weight));

    return synapse_structure_update_state(
        synapse_structure_get_eligibility_trace(*current_state),
        new_weight);
}

//---------------------------------------
static inline index_t _sparse_axonal_delay(uint32_t x) {
    return ((x >> synapse_delay_index_type_bits) & SYNAPSE_AXONAL_DELAY_MASK);
}

address_t synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    // Load timing dependence data
    address_t weight_region_address = timing_initialise(address);
    if (address == NULL) {
        return NULL;
    }

    // Read Izhikevich weight update equation constant component
    weight_update_constant_component = *weight_region_address++;

    // Load weight dependence data
    address_t weight_result = weight_initialise(
        weight_region_address, n_synapse_types,
        ring_buffer_to_input_buffer_left_shifts);
    if (weight_result == NULL) {
        return NULL;
    }

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        return NULL;
    }

    uint32_t n_neurons_power_2 = n_neurons;
    uint32_t log_n_neurons = 1;
    if (n_neurons != 1) {
    	if (!is_power_of_2(n_neurons)) {
    		n_neurons_power_2 = next_power_of_2(n_neurons);
    	}
    	log_n_neurons = ilog_2(n_neurons_power_2);
    }

    uint32_t n_synapse_types_power_2 = n_synapse_types;
    if (!is_power_of_2(n_synapse_types)) {
        n_synapse_types_power_2 = next_power_of_2(n_synapse_types);
    }
    uint32_t log_n_synapse_types = ilog_2(n_synapse_types_power_2);

    synapse_type_index_bits = log_n_neurons + log_n_synapse_types;
    synapse_type_index_mask = (1 << synapse_type_index_bits) - 1;
    synapse_index_bits = log_n_neurons;
    synapse_index_mask = (1 << synapse_index_bits) - 1;
    synapse_delay_index_type_bits =
        SYNAPSE_DELAY_BITS + synapse_type_index_bits;
    synapse_type_mask = (1 << log_n_synapse_types) - 1;

    return weight_result;
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
    return ((x >> synapse_delay_index_type_bits) & SYNAPSE_AXONAL_DELAY_MASK);
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
                                                     last_post_trace), false);
}

//--------------------------------------
void synapse_dynamics_process_neuromodulator_event(
        uint32_t time, int32_t concentration, uint32_t neuron_index,
        uint32_t synapse_type) {
    log_debug(
        "Adding neuromodulation event to trace at time:%u concentration:%d",
        time, concentration);

    // Get post event history of this neuron
    post_event_history_t *history = &post_event_history[neuron_index];
    const uint32_t last_post_time = history->times[history->count_minus_one];
    const post_trace_t last_post_trace =
        history->traces[history->count_minus_one];

    // Add a new history trace into the buffer of post synaptic events
    post_events_add(time, history, add_dopamine_spike(time,
        concentration, last_post_time, last_post_trace, synapse_type), true);
}

//---------------------------------------
bool synapse_dynamics_process_plastic_synapses(address_t plastic,
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
        uint32_t delay_dendritic = synapse_row_sparse_delay(control_word,
            synapse_type_index_bits);
        uint32_t delay_axonal = 0;//sparse_axonal_delay(control_word);
        uint32_t type_index = synapse_row_sparse_type_index(control_word,
            synapse_type_index_mask);

        // Convert into ring buffer offset
        uint32_t offset = synapses_get_ring_buffer_index_combined(
            delay_axonal + delay_dendritic + time, type_index,
            synapse_type_index_bits);

        uint32_t type = synapse_row_sparse_type(
            control_word, synapse_index_bits, synapse_type_mask);
        uint32_t index = synapse_row_sparse_index(
            control_word, synapse_index_mask);

       // Get state of synapse - weight and eligibility trace.
       plastic_synapse_t* current_state = plastic_words;
       weight_state = weight_get_initial(
           synapse_structure_get_weight(*current_state), type);

       // Update the synapse state
       plastic_synapse_t final_state = plasticity_update_synapse(time,
           last_pre_time, last_pre_trace,
           event_history->prev_trace, delay_dendritic, delay_axonal,
           current_state, &post_event_history[index]);

       // Add weight to ring-buffer entry
       ring_buffer[offset] += synapse_structure_get_weight(final_state);

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

uint32_t synapse_dynamics_get_plastic_saturation_count(){
    return plastic_saturation_count;
}

#if SYNGEN_ENABLED == 1

//! \brief  Searches the synaptic row for the the connection with the
//!         specified post-synaptic ID
//! \param[in] id: the (core-local) ID of the neuron to search for in the
//! synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[out] sp_data: the address of a struct through which to return
//! weight, delay information
//! \return bool: was the search successful?
bool find_plastic_neuron_with_id(uint32_t id, address_t row,
                                 structural_plasticity_data_t *sp_data){
    address_t fixed_region = synapse_row_fixed_region(row);
    address_t plastic_region_address = synapse_row_plastic_region(row);
    plastic_synapse_t *plastic_words =
        _plastic_synapses(plastic_region_address);
    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);
    plastic_synapse_t weight;
    uint32_t delay;

    // Loop through plastic synapses
    bool found = false;
    for (; plastic_synapse > 0; plastic_synapse--) {

        // Get next control word (auto incrementing)
        weight = *plastic_words++;
        uint32_t control_word = *control_words++;

        // Check if index is the one I'm looking for
        delay = synapse_row_sparse_delay(control_word, synapse_type_index_bits);
        if (synapse_row_sparse_index(control_word, synapse_index_mask)==id) {
            found = true;
            break;
        }
    }

    if (found){
        sp_data -> weight = weight;
        sp_data -> offset = synapse_row_num_plastic_controls(fixed_region) -
            plastic_synapse;
        sp_data -> delay  = delay;
        return true;
        }
    else{
        sp_data -> weight = -1;
        sp_data -> offset = -1;
        sp_data -> delay  = -1;
        return false;
        }
}

//! \brief  Remove the entry at the specified offset in the synaptic row
//! \param[in] offset: the offset in the row at which to remove the entry
//! \param[in] row: the core-local address of the synaptic row
//! \return bool: was the removal successful?
bool remove_plastic_neuron_at_offset(uint32_t offset, address_t row){
    address_t fixed_region = synapse_row_fixed_region(row);
    plastic_synapse_t *plastic_words =
        _plastic_synapses(synapse_row_plastic_region(row));
    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Delete weight at offset
    plastic_words[offset] =  plastic_words[plastic_synapse-1];
    plastic_words[plastic_synapse-1] = 0;

   // Delete control word at offset
    control_words[offset] = control_words[plastic_synapse-1];
    control_words[plastic_synapse-1] = 0;

    // Decrement FP
    fixed_region[1] = fixed_region[1] - 1;

    return true;
}

//! ensuring the weight is of the correct type and size
static inline plastic_synapse_t _weight_conversion(uint32_t weight){
    return (plastic_synapse_t)(0xFFFF & weight);
}

//! packing all of the information into the required plastic control word
static inline control_t _control_conversion(uint32_t id, uint32_t delay,
                                            uint32_t type){
    control_t new_control =
        ((delay & ((1<<SYNAPSE_DELAY_BITS) - 1)) << synapse_type_index_bits);
    new_control |= (type & ((1<<synapse_type_index_bits) - 1)) << synapse_index_bits;
    new_control |= (id & ((1<<synapse_index_bits) - 1));
    return new_control;
}

//! \brief  Add a plastic entry in the synaptic row
//! \param[in] id: the (core-local) ID of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return bool: was the addition successful?
bool add_plastic_neuron_with_id(uint32_t id, address_t row,
        uint32_t weight, uint32_t delay, uint32_t type){
    plastic_synapse_t new_weight = _weight_conversion(weight);
    control_t new_control = _control_conversion(id, delay, type);

    address_t fixed_region = synapse_row_fixed_region(row);
    plastic_synapse_t *plastic_words =
        _plastic_synapses(synapse_row_plastic_region(row));
    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Add weight at offset
    plastic_words[plastic_synapse] = new_weight;

    // Add control word at offset
    control_words[plastic_synapse] = new_control;

    // Increment FP
    fixed_region[1] = fixed_region[1] + 1;
    return true;
}
#endif
