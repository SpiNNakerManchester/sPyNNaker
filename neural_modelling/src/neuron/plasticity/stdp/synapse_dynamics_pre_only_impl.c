// Spinn_common includes
#include "static-assert.h"

// sPyNNaker neural modelling includes
#include "../../synapses.h"
#include "../synapse_dynamics.h"

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

//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
    pre_trace_t prev_trace;
    uint32_t prev_time;
} pre_event_history_t;

post_event_history_t *post_event_history;

// Pointers to neuron data
static neuron_pointer_t neuron_array_plasticity;
static additional_input_pointer_t additional_input_array_plasticity;
static threshold_type_pointer_t threshold_type_array_plasticity;

//---------------------------------------
// Synapse update loop
//---------------------------------------


// Helper function to perform update based only on pre-spike
final_state_t _update_on_pre_only(
		uint32_t time,
		const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
		const pre_trace_t new_pre_trace, const uint32_t delay_dendritic,
		const uint32_t delay_axonal, update_state_t current_state,
		const uint32_t syn_type,
        const post_event_history_t *post_event_history,
		neuron_pointer_t post_synaptic_neuron,
		additional_input_pointer_t post_synaptic_additional_input,
        threshold_type_pointer_t post_synaptic_threshold) {

	// Apply axonal delay to time of last presynaptic spike
	    const uint32_t delayed_last_pre_time = last_pre_time + delay_axonal;

    const uint32_t window_begin_time = (delayed_last_pre_time >= delay_dendritic) ?
        (delayed_last_pre_time - delay_dendritic) : 0;
    const uint32_t window_end_time = time + delay_axonal - delay_dendritic;
	post_event_window_t post_window = post_events_get_window_delayed(
	            post_event_history, window_begin_time, window_end_time);

	// for Fusi rule call weight_apply_potentiation and weight_apply_depression based on
	// post-synaptic neuron voltage
	current_state = timing_apply_pre_spike(
	        time, new_pre_trace, last_pre_time, last_pre_trace,
	        post_window.prev_time, post_window.prev_trace, current_state,
			syn_type, post_synaptic_neuron,	post_synaptic_additional_input,
	         post_synaptic_threshold);

	// update the weight and return
	final_state_t final = synapse_structure_get_final_state(current_state);

	return final;
}

static inline final_state_t _plasticity_update_synapse(
        uint32_t time,
        const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
        const pre_trace_t new_pre_trace, const uint32_t delay_dendritic,
        const uint32_t delay_axonal, update_state_t current_state,
        const post_event_history_t *post_event_history) {

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
    /*
    // Process events in post-synaptic window
    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time = *post_window.next_time
                                           + delay_dendritic;
        log_debug("\t\tApplying post-synaptic event at delayed time:%u\n",
              delayed_post_time);

        // Apply spike to state
        current_state = timing_apply_post_spike(
            delayed_post_time, *post_window.next_trace, delayed_last_pre_time,
            last_pre_trace, post_window.prev_time, post_window.prev_trace,
            current_state);

        // Go onto next event
        post_window = post_events_next_delayed(post_window, delayed_post_time);
    }

    const uint32_t delayed_pre_time = time + delay_axonal;
    log_debug("\t\tApplying pre-synaptic event at time:%u last post time:%u\n",
              delayed_pre_time, post_window.prev_time);

    // Apply spike to state
    // **NOTE** dendritic delay is subtracted
    current_state = timing_apply_pre_spike(
        delayed_pre_time, new_pre_trace, delayed_last_pre_time, last_pre_trace,
        post_window.prev_time, post_window.prev_trace, current_state);
	*/
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

address_t synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    // Load timing dependence data
    address_t weight_region_address = timing_initialise(address);
    if (address == NULL) {
        return NULL;
    }

    // Load weight dependence data
    address_t weight_result = weight_initialise(
        weight_region_address, ring_buffer_to_input_buffer_left_shifts);
    if (weight_result == NULL) {
        return NULL;
    }

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        return NULL;
    }

    return weight_result;
}

bool synapse_dynamics_process_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        weight_t *ring_buffers, uint32_t time) {

    log_debug("time: %d ", time);

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
    const uint32_t last_pre_time = event_history->prev_time;
    const pre_trace_t last_pre_trace = event_history->prev_trace;

    // Update pre-synaptic trace
    log_debug("Adding pre-synaptic event to trace at time:%u", time);
    event_history->prev_time = time;
    event_history->prev_trace = timing_add_pre_spike(time, last_pre_time,
                                                     last_pre_trace);

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

        // Get data structures for this synapse's post-synaptic neuron
        neuron_pointer_t post_synaptic_neuron = &neuron_array_plasticity[index];
        additional_input_pointer_t post_synaptic_additional_input =
                		&additional_input_array_plasticity[index];
        threshold_type_pointer_t post_synaptic_threshold = &threshold_type_array_plasticity[index];

        // for integration test
        log_debug("time: %u, neuron index: %u, threshold_value: %k, membrane voltage:, %k",
        		time, index, post_synaptic_threshold->threshold_value,
				post_synaptic_neuron->V_membrane);

        // Create update state from the plastic synaptic word
        update_state_t current_state = synapse_structure_get_update_state(
            *plastic_words, type);

        //neuron_pointer_t neuron = neuron_array_stdp;
        log_debug("Neuron Voltage: %11.4k", neuron_model_get_membrane_voltage(post_synaptic_neuron));

        final_state_t final_state = _update_on_pre_only(time, last_pre_time,
        		last_pre_trace, event_history->prev_trace,
                delay_dendritic, delay_axonal, current_state, type,
            &post_event_history[index], post_synaptic_neuron,
			post_synaptic_additional_input, post_synaptic_threshold);


        /*
        // Update the synapse state
        final_state_t final_state = _plasticity_update_synapse(
            time, last_pre_time, last_pre_trace, event_history->prev_trace,
            delay_dendritic, delay_axonal, current_state,
            &post_event_history[index]);
        */

        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
                delay_axonal + delay_dendritic + time, type_index);

        // Add weight to ring-buffer entry
        // **NOTE** Dave suspects that this could be a
        // potential location for overflow
        ring_buffers[ring_buffer_index] += synapse_structure_get_final_weight(
            final_state);

        // Write back updated synaptic word to plastic region
        *plastic_words++ = synapse_structure_get_final_synaptic_word(
            final_state);
    }
#ifdef _LOG_FIG1_
    log_info("time: %d ", time);
#endif

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

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(){
    return num_plastic_pre_synaptic_events;
}

void synapse_dynamics_set_neuron_array(neuron_pointer_t neuron_array){
	neuron_array_plasticity = neuron_array;
}

void synapse_dynamics_set_threshold_array(threshold_type_pointer_t threshold_type_array){
	threshold_type_array_plasticity = threshold_type_array;
}

void synapse_dynamics_set_additional_input_array(additional_input_pointer_t additional_input_array){
	additional_input_array_plasticity = additional_input_array;
}
