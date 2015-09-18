// Spinn_common includes
#include "static-assert.h"

// sPyNNaker neural modelling includes
#include "../../synapses.h"

// Plasticity common includes
#include <string.h>
#include <debug.h>

#ifdef SYNAPSE_BENCHMARK
  uint32_t num_plastic_pre_synaptic_events = 0;
#endif  // SYNAPSE_BENCHMARK

//-----------------------------------------------------------------------------
// Structures
//-----------------------------------------------------------------------------
typedef struct {
    stp_trace_t stp_trace;
    uint32_t prev_time;
} pre_event_history_t;

//-----------------------------------------------------------------------------
// Synaptic row plastic-region implementation
//-----------------------------------------------------------------------------
static inline weight_t* _plastic_synapses(
        address_t plastic_region_address) {
    const uint32_t pre_event_history_size_words =
        sizeof(pre_event_history_t) / sizeof(uint32_t);
    static_assert(pre_event_history_size_words * sizeof(uint32_t)
                  == sizeof(pre_event_history_t),
                  "Size of pre_event_history_t structure should be a multiple"
                  " of 32-bit words");

    return (weight_t*)
        (&plastic_region_address[pre_event_history_size_words]);
}

//-----------------------------------------------------------------------------
static inline pre_event_history_t *_plastic_event_history(
        address_t plastic_region_address) {
    return (pre_event_history_t*) (&plastic_region_address[0]);
}
//-----------------------------------------------------------------------------
void synapse_dynamics_print_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(plastic_region_address);
    use(fixed_region_address);
    use(ring_buffer_to_input_buffer_left_shifts);
#if LOG_LEVEL >= LOG_DEBUG

    // Extract seperate arrays of weights (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    weight_t *plastic_words = _plastic_synapses(plastic_region_address);
    const control_t *control_words = synapse_row_plastic_controls(
        fixed_region_address);
    size_t plastic_synapse = synapse_row_num_plastic_controls(
        fixed_region_address);
    const pre_event_history_t *event_history = _plastic_event_history(
        plastic_region_address);

    log_debug("Plastic region %u synapses\n", plastic_synapse);

    // Loop through plastic synapses
    for (uint32_t i = 0; i < plastic_synapse; i++) {

        // Get next weight and control word (autoincrementing control word)
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
//-----------------------------------------------------------------------------
bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(n_neurons);
    use(ring_buffer_to_input_buffer_left_shifts);
    // Load STP data
    stp_initialise(address);
    if (address == NULL) {
        return false;
    }

    return true;
}
//-----------------------------------------------------------------------------
bool synapse_dynamics_process_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        weight_t *ring_buffers, uint32_t time, bool flush) {

    // Extract seperate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    const weight_t *plastic_words = _plastic_synapses(
        plastic_region_address);
    const control_t *control_words = synapse_row_plastic_controls(
        fixed_region_address);
    size_t plastic_synapse = synapse_row_num_plastic_controls(
        fixed_region_address);

#ifdef SYNAPSE_BENCHMARK
    num_plastic_pre_synaptic_events += plastic_synapse;
#endif  // SYNAPSE_BENCHMARK

    // Get event history from synaptic row
    pre_event_history_t *event_history = _plastic_event_history(
        plastic_region_address);

    // Get last pre-synaptic event from event history
    stp_result_t stp_result = stp_add_pre_spike(time, event_history->prev_time, event_history->stp_trace);

    // Update pre-synaptic trace
    log_debug("Adding pre-synaptic event to trace at time:%u (flush:%u)",
              time, flush);
    event_history->prev_time = time;
    event_history->stp_trace = stp_result.trace;

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {
        // Get next control word and weight (autoincrementing)
        uint32_t control_word = *control_words++;
        uint32_t weight = *plastic_words++;

        // Extract control-word components
        uint32_t delay = synapse_row_sparse_delay(control_word);
        uint32_t type_index = synapse_row_sparse_type_index(control_word);

        // Calculate delayed offset into ring buffer
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
            delay + time, type_index);

        // Add weight to ring-buffer entry
        // **NOTE** Dave suspects that this could be a
        // potential location for overflow
        ring_buffers[ring_buffer_index] += stp_apply(weight,
                                                     stp_result.update_state);
    }
    return true;
}
//-----------------------------------------------------------------------------
void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
}
//-----------------------------------------------------------------------------
input_t synapse_dynamics_get_intrinsic_bias(uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
    return 0.0k;
}
//-----------------------------------------------------------------------------
//! \either prints the counters for plastic pre synaptic events based
//! on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or does
//! nothing (the assumption being that a empty function will be removed by the
//! compiler and therefore there is no code bloat)
//! \return Nothing, this method does not return anything
void synapse_dynamics_print_plastic_pre_synaptic_events(){
#ifdef SYNAPSE_BENCHMARK
    log_info("\t%u plastic pre-synaptic events.",
        num_plastic_pre_synaptic_events);
#endif  // SYNAPSE_BENCHMARK
}
