// Spinn_common includes
#include "static-assert.h"

// sPyNNaker neural modelling includes
#include "../../synapses.h"

// Plasticity common includes
#include "../common/pre_events.h"
#include "../common/post_events.h"

#include "weight_dependence/weight.h"
#include "timing_dependence/timing.h"
#include <string.h>
#include <debug.h>

uint32_t num_plastic_pre_synaptic_events;

post_event_history_t *post_event_history;

//---------------------------------------
// Synapse update loop
//---------------------------------------
static inline final_state_t _plasticity_update_synapse(
        uint32_t time, uint32_t begin_time,
        uint32_t delay, update_state_t current_state,
        const pre_event_history_t *pre_event_history,
        const post_event_history_t *post_event_history) {

    // Get the pre-synaptic window of events to be processed
    pre_event_window_t pre_window = pre_events_get_window(
        time, pre_event_history, delay, begin_time);

    // Get the post-synaptic window of events to be processed
    post_event_window_t post_window = post_events_get_window(
        post_event_history, begin_time);

    log_debug("\tPerforming deferred synapse update at time:%u"
              " - pre_window.prev_time:%u, pre_window.num_events:%u,"
              " post_window.prev_time:%u, post_window.num_events:%u",
              time, pre_window.prev_time, pre_window.num_events,
              post_window.prev_time, post_window.num_events);

    // Process events that occur within window
    while (true) {
        // Are the next pre and post-synaptic events valid?
        const bool pre_valid = (pre_window.num_events > 0);
        const bool post_valid = (post_window.num_events > 0);

        // If next pre-synaptic event occurs before the next post-synaptic event
        if (pre_valid
                && (!post_valid
                        || (*pre_window.next_time + delay)
                                <= *post_window.next_time)) {
            log_debug("\t\tApplying pre-synaptic event at time:%u",
                      *pre_window.next_time + delay);

            // Apply spike to state
            const uint32_t delayed_pre_time = *pre_window.next_time + delay;
            current_state = timing_apply_pre_spike(delayed_pre_time,
                    *pre_window.next_trace, pre_window.prev_time,
                    pre_window.prev_trace, post_window.prev_time,
                    post_window.prev_trace, current_state);

            // Go onto next event
            pre_window = pre_events_next(pre_window, delayed_pre_time);
        }
        // Otherwise, if the next post-synaptic event occurs before the next pre-synaptic event
        else if (post_valid
                && (!pre_valid
                        || *post_window.next_time
                                <= (*pre_window.next_time + delay))) {
            log_debug("\t\tApplying post-synaptic event at time:%u",
                      *post_window.next_time);

            // Apply spike to state
            current_state = timing_apply_post_spike(*post_window.next_time,
                    *post_window.next_trace, pre_window.prev_time,
                    pre_window.prev_trace, post_window.prev_time,
                    post_window.prev_trace, current_state);

            // Go onto next event
            post_window = post_events_next(post_window);
        }
        // Otherwise, there's no more events so stop
        else {
            break;
        }
    }

    // Return final synaptic word and weight
    return synapse_structure_get_final_state(current_state);
}

//---------------------------------------
// Synaptic row plastic-region implementation
//---------------------------------------
static inline plastic_synapse_t* _plastic_synapses(
        address_t plastic_region_address) {
    const uint32_t pre_event_history_size_words =
        sizeof(pre_event_history_t) / sizeof(uint32_t);
    static_assert(pre_event_history_size_words * sizeof(uint32_t)
                  == sizeof(pre_event_history_t),
                  "Size of pre_event_history_t structure should be a multiple"
                  " of 32-bit words");

    return (plastic_synapse_t*)
        (&plastic_region_address[pre_event_history_size_words]);
}

//---------------------------------------
static inline pre_event_history_t *_plastic_event_history(
        address_t plastic_region_address) {
    return (pre_event_history_t*) (&plastic_region_address[0]);
}

//---------------------------------------
bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    // Load timing dependence data
    address_t weight_region_address = timing_initialise(address);
    if (address == NULL) {
        return false;
    }

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

bool synapse_dynamics_process_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        weight_t *ring_buffers, uint32_t time) {

    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    plastic_synapse_t *plastic_words = _plastic_synapses(
        plastic_region_address);
    const control_t *control_words = synapse_row_plastic_controls(
        fixed_region_address);
    size_t plastic_synapse = synapse_row_num_plastic_controls(
        fixed_region_address);

    num_plastic_pre_synaptic_events += plastic_synapse;

    // Get event history from synaptic row
    pre_event_history_t *event_history = _plastic_event_history(
        plastic_region_address);

    // Get last pre-synaptic event from event history
    // **NOTE** at this level we don't care about individual synaptic delays
    const uint32_t last_pre_time =
            event_history->times[event_history->count_minus_one];

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {

        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        // Extract control-word components
        // **NOTE** cunningly, control word is just the same as lower
        // 16-bits of 32-bit fixed synapse so same functions can be used
        uint32_t delay = synapse_row_sparse_delay(control_word);
        uint32_t type = synapse_row_sparse_type(control_word);
        uint32_t index = synapse_row_sparse_index(control_word);
        uint32_t type_index = synapse_row_sparse_type_index(control_word);

        // Create update state from the plastic synaptic word
        update_state_t current_state = synapse_structure_get_update_state(
            *plastic_words, type);

        // Update the synapse state
        final_state_t final_state = _plasticity_update_synapse(
            time, last_pre_time, delay, current_state, event_history,
            &post_event_history[index]);

        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
            delay + time, type_index);

        // Add weight to ring-buffer entry
        // **NOTE** Dave suspects that this could be a potential location
        // for overflow
        ring_buffers[ring_buffer_index] += synapse_structure_get_final_weight(
            final_state);

        // Write back updated synaptic word to plastic region
        *plastic_words++ = synapse_structure_get_final_synaptic_word(
            final_state);
    }

    log_debug("Adding pre-synaptic event to trace at time:%u", time);

    // Add pre-event
    const pre_trace_t last_pre_trace =
        event_history->traces[event_history->count_minus_one];
    pre_events_add(time, event_history, timing_add_pre_spike(
        time, last_pre_time, last_pre_trace));

    return true;
}

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

input_t synapse_dynamics_get_intrinsic_bias(uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
    return 0.0k;
}

void synapse_dynamics_print_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(plastic_region_address);
    use(fixed_region_address);
    use(ring_buffer_to_input_buffer_left_shifts);
#if LOG_LEVEL >= LOG_DEBUG

    // Extract separate arrays of weights (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    weight_t *plastic_words = _plastic_synapses(plastic_region_address);
    const control_t *control_words = synapse_row_plastic_controls(
        fixed_region_address);
    size_t plastic_synapse = synapse_row_num_plastic_controls(
        fixed_region_address);
    const pre_event_history_t *event_history = _plastic_event_history(
        plastic_region_address);

    log_debug(
        "Plastic region %u synapses pre-synaptic event buffer count:%u:\n",
        plastic_synapse, event_history->count_minus_one + 1);

    // Loop through plastic synapses
    for (uint32_t i = 0; i < plastic_synapse; i++) {

        // Get next weight and control word (auto incrementing control word)
        uint32_t weight = *plastic_words++;
        uint32_t control_word = *control_words++;
        uint32_t synapse_type = synapse_row_sparse_type(control_word);

        log_debug("%08x [%3d: (w: %5u (=", control_word, i, weight);
        synapses_print_weight(
            weight, ring_buffer_to_input_buffer_left_shifts[synapse_type]);
        log_debug("nA) d: %2u, %s, n = %3u)] - {%08x %08x}\n",
                  synapse_row_sparse_delay(control_word),
                  synapse_types_get_type_char(synapse_row_sparse_type(
                                             control_word)),
                  synapse_row_sparse_index(control_word), SYNAPSE_DELAY_MASK,
                  SYNAPSE_TYPE_INDEX_BITS);
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! \brief returns the counters for plastic pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return counters for plastic pre synaptic events or 0
uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(){
    return num_plastic_pre_synaptic_events;
}
