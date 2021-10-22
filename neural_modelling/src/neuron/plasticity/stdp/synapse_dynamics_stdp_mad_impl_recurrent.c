// Spinn_common includes
#include "static-assert.h"

// sPyNNaker neural modelling includes
#include <neuron/synapses.h>
#include "../synapse_dynamics.h"


// Plasticity includes
#include "maths.h"
#include "post_events_inc_v.h"

#include "weight_dependence/weight.h"
#include "timing_dependence/timing.h"
//#include <string.h>
#include <debug.h>
#include <utils.h>
#include <neuron/plasticity/synapse_dynamics.h>
#include <neuron/additional_inputs/additional_input_none_impl.h>
#include <neuron/models/neuron_model.h>
#include <neuron/models/neuron_model_lif_v_hist_impl.h>

extern neuron_pointer_t neuron_array;

#ifndef print_plasticity
#define print_plasticity false
#error should have beend defined in synapse_dynamics
#endif


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
static inline final_state_t _plasticity_update_synapse(
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

    // Get the post-synaptic window of events to be processed
    const uint32_t window_begin_time = (delayed_last_pre_time >=
        delay_dendritic) ? (delayed_last_pre_time - delay_dendritic ) : 0;
    const uint32_t window_end_time = time + delay_axonal - delay_dendritic ;
    post_event_window_t post_window = post_events_get_window_delayed(
            post_event_history, window_begin_time, window_end_time);

    log_debug("\tPerforming deferred synapse update at time:%u", time);
    log_debug("\t\tbegin_time:%u, end_time:%u - prev_time:%u, num_events:%u",
        window_begin_time, window_end_time, post_window.prev_time,
        post_window.num_events);


     //io_printf(IO_BUF, "PRINTING ENTIRE HISTORY\n");
     //print_event_history(post_event_history);

     //io_printf(IO_BUF, "PRINTING WINDOW \n");
     //print_delayed_window_events(post_event_history, window_begin_time,
     // 		window_end_time, delay_dendritic);

    // Process events in post-synaptic window
    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time = *post_window.next_time
                                           + delay_dendritic;
        if (print_plasticity){
        	io_printf(IO_BUF, "\t\tApplying post-synaptic event at delayed time:%u\n",
              delayed_post_time);
        }

        // Apply spike to state
        current_state = timing_apply_post_spike(
            delayed_post_time, *post_window.next_trace, delayed_last_pre_time,
            last_pre_trace, post_window.prev_time, post_window.prev_trace,
            current_state, syn_type, post_synaptic_neuron,
			post_synaptic_additional_input, post_synaptic_threshold,
			*post_window.next_post_synaptic_v);

        // Go onto next event
        post_window = post_events_next_delayed(post_window, delayed_post_time);
    }


    const uint32_t delayed_pre_time = time + delay_axonal;
    if (print_plasticity){
    	io_printf(IO_BUF, "\t\t Applying pre-synaptic event at time:%u last post time:%u\n",
              delayed_pre_time, post_window.prev_time);
    }

    // Apply spike to state
    // **NOTE** dendritic delay is subtracted
    if (print_plasticity){
    	io_printf(IO_BUF, "Weight is: %u\n", current_state.weight_state.weight);
    }

    //io_printf(IO_BUF, "PRINTING POST HISTORY BEFORE DEPRESSION\n");
    //io_printf(IO_BUF, "Spike: %u, Time: %u, Trace: %u, Mem_V: %k\n",
//		post_window.num_events, post_window.prev_time,
//		post_window.prev_trace, post_window.prev_post_synaptic_v);



 //   io_printf(IO_BUF, "\n\n\n");

    current_state = timing_apply_pre_spike(
        delayed_pre_time, new_pre_trace, delayed_last_pre_time, last_pre_trace,
        post_window.prev_time, post_window.prev_trace, current_state, syn_type,
		post_synaptic_neuron, post_synaptic_additional_input,
		post_synaptic_threshold, post_window.prev_post_synaptic_v); // SD 25/10/19: use membrane pot for depression, too.

//    io_printf(IO_BUF, "Weight is: %u\n", current_state.weight_state.weight);

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
        uint32_t synapse_type = synapse_row_sparse_type(
            control_word, synapse_index_bits, synapse_type_mask);

        log_debug("%08x [%3d: (w: %5u (=", control_word, i, weight);
        synapses_print_weight(
            weight, ring_buffer_to_input_buffer_left_shifts[synapse_type]);
        log_debug("nA) d: %2u, %s, n = %3u)] - {%08x %08x}\n",
                  synapse_row_sparse_delay(
                      control_word, synapse_type_index_bits),
                  synapse_types_get_type_char(synapse_type),
                  synapse_row_sparse_index(control_word, synapse_index_mask),
                  SYNAPSE_DELAY_MASK, synapse_type_index_bits);
    }
#endif // LOG_LEVEL >= LOG_DEBUG
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

bool synapse_dynamics_process_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        weight_t *ring_buffers, uint32_t time) {

    uint32_t syn_type = 0;
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


    if (plastic_synapse > 0)
    {
        // Get the synapse type from the first synapse in the row:
        syn_type = synapse_row_sparse_type(*control_words, synapse_index_bits, synapse_type_mask);
    }

    // Update pre-synaptic trace
    if (print_plasticity){
        io_printf(IO_BUF, "                Adding pre-synaptic event to trace at time:%u\n", time);
    }
    event_history->prev_time = time;
    event_history->prev_trace = timing_add_pre_spike_sd(time, last_pre_time,
                                                     last_pre_trace, syn_type);

    // Loop through plastic synapses
    for (; plastic_synapse > 0; plastic_synapse--) {

        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        // Extract control-word components
        // **NOTE** cunningly, control word is just the same as lower
        // 16-bits of 32-bit fixed synapse so same functions can be used
        uint32_t delay_axonal = _sparse_axonal_delay(control_word);
        uint32_t delay_dendritic = synapse_row_sparse_delay(
            control_word, synapse_type_index_bits);
        uint32_t type = synapse_row_sparse_type(
            control_word, synapse_index_bits, synapse_type_mask);
        uint32_t index = synapse_row_sparse_index(
            control_word, synapse_index_mask);
        uint32_t type_index = synapse_row_sparse_type_index(
            control_word, synapse_type_index_mask);

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

//        io_printf(IO_BUF, "Initial weight is: %u\n", current_state.weight_state.weight);

        uint32_t full_delay = delay_dendritic;
        delay_dendritic = 10; // SD 2ms! //10; // SD 1.0 ms back propo time at 0.1 ms time step

        // Update the synapse state
        final_state_t final_state = _plasticity_update_synapse(
            time, last_pre_time, last_pre_trace, event_history->prev_trace,
            delay_dendritic, delay_axonal, current_state, type,
            &post_event_history[index], post_synaptic_neuron,
			post_synaptic_additional_input, post_synaptic_threshold);

        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
                //delay_axonal + delay_dendritic + time, type_index,
                delay_axonal + full_delay + time, type_index,
                synapse_type_index_bits);

        int32_t accumulation = ring_buffers[ring_buffer_index] +
                synapse_structure_get_final_weight(final_state);

//        uint32_t sat_test = accumulation & 0x10000;
//        if (sat_test){
//            accumulation = sat_test - 1;
//            plastic_saturation_count += 1;
//        }

//        io_printf(IO_BUF, "Adding weight: %u \n", accumulation);

        ring_buffers[ring_buffer_index] = accumulation;

        // Write back updated synaptic word to plastic region
        *plastic_words++ = synapse_structure_get_final_synaptic_word(
            final_state);
    }
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
    post_events_add_inc_v(time, history, timing_add_post_spike(
    		time, last_post_time, last_post_trace),
    		neuron_array_plasticity[neuron_index].V_mem_hist);

    // either set here in the post-synaptic history so we can log the membrane
    // potential a few timesteps before - i.e. before teacher input caused spike
    // but how do we know how long before spike we need? Do we assume that the
    // teacher input causes a spike in literally the next timestep? Is it better
    // record the potential immediately before the teacher input begins to have effect?
    // history->v_before_last_teacher_pre = neuron_array_plasticity[neuron_index].V_mem_hist;

}

input_t synapse_dynamics_get_intrinsic_bias(uint32_t time,
                                            index_t neuron_index) {
    use(time);
    use(neuron_index);
    return 0.0k;
}

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events(){
    return num_plastic_pre_synaptic_events;
}

uint32_t synapse_dynamics_get_plastic_saturation_count(){
    return plastic_saturation_count;
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
