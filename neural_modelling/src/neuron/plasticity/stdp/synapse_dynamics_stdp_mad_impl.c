
// sPyNNaker neural modelling includes
#include "../../synapses.h"

// Plasticity common includes
#include "../common/maths.h"

#include "post_events.h"
#include "stdp_rule.h"
#include <string.h>
#include <debug.h>

uint32_t num_plastic_pre_synaptic_events = 0;

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

#define SYNAPSE_DELAY_TYPE_INDEX_BITS \
    (SYNAPSE_DELAY_BITS + SYNAPSE_TYPE_INDEX_BITS)

#if (SYNAPSE_DELAY_TYPE_INDEX_BITS + SYNAPSE_AXONAL_DELAY_BITS) > 16
#error "Not enough bits for axonal synaptic delay bits"
#endif

// Post-event history - array of one per post-synaptic neuron (on this core).
post_event_history_t *post_event_history;

// Scaling of weights - one value per synapse type
accum *weight_scales;

// For calculating the time in milliseconds
accum time_step_ms;

//---------------------------------------
// Synapse update loop
//---------------------------------------
static inline void _plasticity_update_synapse(
        const uint32_t time, const uint32_t last_pre_time,
        const post_event_history_t *post_event_history,
        const uint32_t delay_dendritic, const uint32_t delay_axonal,
        const plastic_synapse_t *plastic_synapse) {

    // Apply axonal delay to time of last presynaptic spike
    const uint32_t delayed_last_pre_time = last_pre_time + delay_axonal;

    // Get the post-synaptic window of events to be processed
    const uint32_t window_begin_time = (delayed_last_pre_time >= delay_dendritic) ?
        (delayed_last_pre_time - delay_dendritic) : 0;
    const uint32_t window_end_time = time + delay_axonal - delay_dendritic;
    post_event_window_t post_window = post_events_get_window_delayed(
            post_event_history, window_begin_time, window_end_time);

    log_debug("\tPerforming deferred synapse update at time:%u", time);
    log_debug("\t\tbegin_time:%u, end_time:%u - prev_time:%u, num_events:%u",
        window_begin_time, window_end_time, post_window.prev_time,
        post_window.num_events);

    // Process events in post-synaptic window
    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time =
                *post_window.next_time + delay_dendritic;
        log_debug("\t\tApplying post-synaptic event at delayed time:%u\n",
              delayed_post_time);

        // Run on_post_synaptic_spike event handler
        stdp_on_postsynaptic_spike(
            plastic_synapse, delayed_post_time * time_step_ms);

        // Go onto next event
        post_window = post_events_next_delayed(post_window, delayed_post_time);
    }

    const uint32_t delayed_pre_time = time + delay_axonal;
    log_debug("\t\tApplying pre-synaptic event at time:%u last post time:%u\n",
              delayed_pre_time, post_window.prev_time);

    // Run on_presynaptic_spike event handler
    // **NOTE** dendritic delay is subtracted
    stdp_on_presynaptic_spike(
        plastic_synapse, delayed_pre_time * time_step_ms);

    // Apply boolean rules
    stdp_do_boolean_checks(plastic_synapse);
}

// Plastic row starts with the last pre-synaptic spike time
static inline plastic_synapse_t* _plastic_synapses(
        address_t plastic_region_address) {
    return &(plastic_region_address[1]);
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

    log_debug("Plastic region %u synapses\n", plastic_synapse);

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
                  synapse_types_get_type_char(synapse_row_sparse_type(control_word)),
                  synapse_row_sparse_index(control_word), SYNAPSE_DELAY_MASK,
                  SYNAPSE_TYPE_INDEX_BITS);
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}

//---------------------------------------
static inline index_t _sparse_axonal_delay(uint32_t x) {
    return ((x >> SYNAPSE_DELAY_TYPE_INDEX_BITS) & SYNAPSE_AXONAL_DELAY_MASK);
}

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        accum* synapse_type_weight_scales) {

    // Copy the weight scales
    weight_scales = synapse_type_weight_scales;

    // Copy the time step
    spin1_memcpy(&time_step_ms, address, sizeof(accum));

    // Initialise the rule
    stdp_init(&address[1]);

    // Initialise the post-even history
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
    uint32_t last_pre_time = plastic_region_address[0];
    plastic_region_address[0] = time;
    plastic_synapse_t *plastic_words = _plastic_synapses(
        plastic_region_address);
    const control_t *control_words = synapse_row_plastic_controls(
        fixed_region_address);
    size_t plastic_synapse = synapse_row_num_plastic_controls(
        fixed_region_address);

    num_plastic_pre_synaptic_events += plastic_synapse;

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {

        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        // Extract control-word components
        // **NOTE** cunningly, control word is just the same as lower
        // 16-bits of 32-bit fixed synapse so same functions can be used
        uint32_t delay_axonal = 0;    //_sparse_axonal_delay(control_word);
        uint32_t delay_dendritic = synapse_row_sparse_delay(control_word);
        uint32_t type = synapse_row_sparse_type(control_word);
        uint32_t index = synapse_row_sparse_index(control_word);
        uint32_t type_index = synapse_row_sparse_type_index(control_word);

        // Update the synapse state
        _plasticity_update_synapse(
            time, last_pre_time, &post_event_history[index],
            delay_dendritic, delay_axonal, &(plastic_words[0]));

        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
                delay_axonal + delay_dendritic + time, type_index);

        // Add weight to ring-buffer entry
        // **NOTE** Dave suspects that this could be a
        // potential location for overflow
        accum weight = stdp_get_weight(&(plastic_words[0]));
        ring_buffers[ring_buffer_index] += weight * weight_scales[type];

        // Move to the next plastic word
        plastic_words++;
    }
    return true;
}

void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    log_debug("Adding post-synaptic event to trace at time:%u", time);

    // Add post-event
    post_event_history_t *history = &post_event_history[neuron_index];
    const uint32_t last_post_time = history->times[history->count_minus_one];
    post_events_add(time, history);
}

input_t synapse_dynamics_get_intrinsic_bias(uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
    return 0.0k;
}

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(){
    return num_plastic_pre_synaptic_events;
}
