/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

//! \file
//! \brief STDP core implementation
#include "post_events.h"
#include "synapse_dynamics_stdp_common.h"
#include "stdp_typedefs.h"
#include <neuron/synapses.h>

#define NUM_MF_SPIKES_TO_RECORD 16

typedef struct {
    uint32_t num_recorded_mf_spikes_minus_one;
    uint32_t mf_times[NUM_MF_SPIKES_TO_RECORD];
    post_trace_t traces[NUM_MF_SPIKES_TO_RECORD];
} pre_event_history_t;

//! The format of the plastic data region of a synaptic row
struct synapse_row_plastic_data_t {
    //! The pre-event history
    pre_event_history_t history;
    //! The per-synapse information
    plastic_synapse_t synapses[];
};

void _print_pre_event_history(pre_event_history_t pre_eve_hist){

	io_printf(IO_BUF, "\n\n************************\n\n");
	io_printf(IO_BUF, "Number recorded MF spikes: %u\n",
	        pre_eve_hist.num_recorded_mf_spikes_minus_one);
	io_printf(IO_BUF, "Prev time: %u\n",
			pre_eve_hist.mf_times[pre_eve_hist.num_recorded_mf_spikes_minus_one]);

	for (int i = 0; i < NUM_MF_SPIKES_TO_RECORD; i++){
		io_printf(IO_BUF, "    Entry %u: %u\n", i, pre_eve_hist.mf_times[i]);
	}
}

//---------------------------------------
// Synapse update loop
//---------------------------------------
static inline final_state_t plasticity_update_synapse(
        const uint32_t time,
        const uint32_t last_pre_time, const pre_trace_t last_pre_trace,
        const pre_trace_t new_pre_trace, uint32_t delay_dendritic,
        const uint32_t delay_axonal, update_state_t current_state,
        const post_event_history_t *post_event_history,
		const pre_event_history_t *pre_event_history) {

    // Apply axonal delay to time of last presynaptic spike
    const uint32_t delayed_last_pre_time = last_pre_time + delay_axonal;

    // Get the post-synaptic window of events to be processed
    const uint32_t window_begin_time = (delayed_last_pre_time >=
        delay_dendritic) ? (delayed_last_pre_time - delay_dendritic) : 0;
    const uint32_t window_end_time = time + delay_axonal - delay_dendritic;
    post_event_window_t post_window = post_events_get_window_delayed(
            post_event_history, window_begin_time, window_end_time);

    log_debug("\tPerforming deferred synapse update at time:%u", time);
    log_debug("\t\tbegin_time:%u, end_time:%u - prev_time:%u, num_events:%u",
        window_begin_time, window_end_time, post_window.prev_time,
        post_window.num_events);

    if (print_plasticity){
    	io_printf(IO_BUF, "    Printing PC history\n");
    	print_event_history(post_event_history);
    }

    if (print_plasticity){
    	io_printf(IO_BUF, "\n############ Phase 1 #############\n");
    	io_printf(IO_BUF, "\n    Looping over PC spikes:\n");
    }

    delay_dendritic = 0;

    // Process events in post-synaptic window
    while (post_window.num_events > 0) {
        const uint32_t delayed_post_time = *post_window.next_time
                                           + delay_dendritic;

        uint32_t mf_begin_time = (delayed_post_time < 255) ? 0 : (delayed_post_time - 255);


        post_event_window_t pre_window = post_events_get_window_delayed(
        		pre_event_history, mf_begin_time, delayed_post_time);

        if (print_plasticity){
        	io_printf(IO_BUF, "    Looping over MF window for this PC spike: %u \n",
                      delayed_post_time);
        }

        while (pre_window.num_events > 0) {

            const uint32_t delayed_pre_time = *pre_window.next_time
                                               + delay_dendritic;

            if (print_plasticity){
            	io_printf(IO_BUF, "        MF Spike: %u \n", delayed_pre_time);

            	io_printf(IO_BUF, "            delta t = %u (delayed MF = %u, delayed PC = %u)\n",
            		delayed_post_time - delayed_pre_time,
					delayed_pre_time,
					delayed_post_time);
            }

        	current_state = timing_apply_post_spike(
        			delayed_post_time, *post_window.next_trace,
					(delayed_post_time - delayed_pre_time),
					last_pre_trace, post_window.prev_time, post_window.prev_trace,
					current_state);

            pre_window = post_events_next_delayed(pre_window, delayed_pre_time);

        }


        // Go onto next event
        post_window = post_events_next_delayed(post_window, delayed_post_time);
    }

    // **************
    // Now look forward to current MF spike from each PC spike.
    const uint32_t fwd_window_begin_time = ((time-delay_dendritic) < 255) ?
    		0 : ((time-delay_dendritic) - 255);

    post_event_window_t fwd_post_window = post_events_get_window_delayed(
                post_event_history, fwd_window_begin_time, window_end_time);


    if (print_plasticity){
    	io_printf(IO_BUF, "\n############ Phase 2 #############\n");
    	io_printf(IO_BUF,
    		"    Looping over all PC spikes and comparing to latest MF spike at: %u\n",
			time+delay_dendritic);
    }

    while (fwd_post_window.num_events > 0) {
    	const uint32_t delayed_mf_time = *fwd_post_window.next_time + delay_dendritic;

    	if (print_plasticity){
    		io_printf(IO_BUF, "        PC spike: %u, dt: %u\n",
    			delayed_mf_time,
				(time+delay_dendritic - delayed_mf_time)
				);
    	}

    	// Some of these variables aren't used
    	current_state = timing_apply_post_spike(
    			delayed_mf_time, *fwd_post_window.next_trace,
				(time+delay_dendritic - delayed_mf_time),
				last_pre_trace, fwd_post_window.prev_time, fwd_post_window.prev_trace,
				current_state);

    	fwd_post_window = post_events_next_delayed(fwd_post_window, delayed_mf_time);
    }

    // **************

    const uint32_t delayed_pre_time = time + delay_axonal;

    if (print_plasticity){
    	log_debug("\t\tApplying pre-synaptic event at time:%u last post time:%u\n",
              delayed_pre_time, post_window.prev_time);
    }

    // Apply spike to state
    // **NOTE** dendritic delay is subtracted
    current_state = timing_apply_pre_spike(
        delayed_pre_time, new_pre_trace, delayed_last_pre_time, last_pre_trace,
        post_window.prev_time, post_window.prev_trace, current_state);

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
static inline index_t _sparse_axonal_delay(uint32_t x) {
#if 1
    // No axonal delay, ever
    __use(x);
    return 0;
#else
    return (x >> synapse_delay_index_type_bits) & SYNAPSE_AXONAL_DELAY_MASK;
#endif
}

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {

    if (!synapse_dynamics_stdp_init(&address, &params, n_synapse_types,
                ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    post_event_history = post_events_init_buffers(n_neurons);
    if (post_event_history == NULL) {
        return false;
    }

    return true;
}

//---------------------------------------
static inline plastic_synapse_t process_plastic_synapse(
        uint32_t control_word, uint32_t last_pre_time, pre_trace_t last_pre_trace,
        pre_trace_t new_pre_trace, weight_t *ring_buffers, uint32_t time,
        plastic_synapse_t synapse, pre_event_history_t *pre_event_history) {
    fixed_stdp_synapse s = synapse_dynamics_stdp_get_fixed(control_word, time);

    // Create update state from the plastic synaptic word
    update_state_t current_state = synapse_structure_get_update_state(
            synapse, s.type);

    // Update the synapse state
    uint32_t post_delay = s.delay_dendritic;

    final_state_t final_state = plasticity_update_synapse(
            time, last_pre_time, last_pre_trace, new_pre_trace,
            post_delay, s.delay_axonal, current_state,
            &post_event_history[s.index], pre_event_history);

    // Add weight to ring-buffer entry
    int32_t weight = synapse_structure_get_final_weight(final_state);
    synapse_dynamics_stdp_update_ring_buffers(ring_buffers, s, weight);

    return synapse_structure_get_final_synaptic_word(final_state);
}

bool synapse_dynamics_process_plastic_synapses(
        synapse_row_plastic_data_t *plastic_region_address,
        synapse_row_fixed_part_t *fixed_region,
        weight_t *ring_buffers, uint32_t time, bool *write_back) {

	if (print_plasticity){
		io_printf(IO_BUF, "\n############ New Plasticity Update #############\n");
	}

    // Extract separate arrays of plastic synapses (from plastic region),
    // Control words (from fixed region) and number of plastic synapses
    plastic_synapse_t *plastic_words = plastic_region_address->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    size_t n_plastic_synapses = synapse_row_num_plastic_controls(fixed_region);

    num_plastic_pre_synaptic_events += n_plastic_synapses;

    // Get last pre-synaptic event from event history
    const uint32_t recorded_spikes_minus_one =
            plastic_region_address->history.num_recorded_mf_spikes_minus_one;
    const uint32_t last_pre_time =
            plastic_region_address->history.mf_times[recorded_spikes_minus_one];

    // no longer need to manage this trace
    const pre_trace_t last_pre_trace = 0;

    // add pre spike to struct capturing pre synaptic event history
    // NOTE: this uses the post_event_history_t handling code
    post_events_add(time, &plastic_region_address->history, 0);

    // Update pre-synaptic trace
    if (print_plasticity){
    	io_printf(IO_BUF,
    		"\nAdding pre-synaptic event (mossy fibre spike) at time: %u\n\n", time);
    }

    timing_add_pre_spike(time, last_pre_time, last_pre_trace);

    // Loop through plastic synapses
    for (; n_plastic_synapses > 0; n_plastic_synapses--) {

        // Get next control word (auto incrementing)
        uint32_t control_word = *control_words++;

        plastic_words[0] = process_plastic_synapse(
                control_word, last_pre_time, last_pre_trace,
                last_pre_trace, ring_buffers, time,
                plastic_words[0], &plastic_region_address->history);
        plastic_words++;
    }

    if (print_plasticity){
    	io_printf(IO_BUF, "\n############ Completed Plasticity Update #############\n");
    }

    *write_back = true;
    return true;
}

void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {

	if (print_plasticity){
		log_debug("Adding post-synaptic event (PC spike)to history at time:%u", time);
	}

    // Add post-event
    post_event_history_t *history = &post_event_history[neuron_index];
    const uint32_t last_post_time = history->times[history->count_minus_one];
    const post_trace_t last_post_trace =
        history->traces[history->count_minus_one];
    post_events_add(time, history, timing_add_post_spike(time, last_post_time,
                                                         last_post_trace));
}

bool synapse_dynamics_find_neuron(
        uint32_t id, synaptic_row_t row, weight_t *weight, uint16_t *delay,
        uint32_t *offset, uint32_t *synapse_type) {
   synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    const synapse_row_plastic_data_t *plastic_data = (void *)
            synapse_row_plastic_region(row);
    const plastic_synapse_t *plastic_words = plastic_data->synapses;
    const control_t *control_words = synapse_row_plastic_controls(fixed_region);
    const size_t n_plastic_synapses = synapse_row_num_plastic_controls(fixed_region);

    // Loop through plastic synapses
    for (size_t plastic_synapse = n_plastic_synapses; plastic_synapse > 0;
            plastic_synapse--) {
        // Take the weight anyway as this updates the plastic words
        *weight = synapse_structure_get_weight(*plastic_words++);

        // Check if index is the one I'm looking for
        uint32_t control_word = *control_words++;
        if (synapse_row_sparse_index(control_word, synapse_index_mask) == id) {
            *offset = n_plastic_synapses - plastic_synapse;
            *delay = synapse_row_sparse_delay(control_word,
                    synapse_type_index_bits, synapse_delay_mask);
            *synapse_type = synapse_row_sparse_type(
                    control_word, synapse_index_bits, synapse_type_mask);
            return true;
        }
    }

    return false;
}

bool synapse_dynamics_remove_neuron(uint32_t offset, synaptic_row_t row) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    synapse_row_plastic_data_t *plastic_data = (void *)
            synapse_row_plastic_region(row);
    plastic_synapse_t *plastic_words = plastic_data->synapses;

    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Delete weight at offset
    plastic_words[offset] =  plastic_words[plastic_synapse - 1];

    // Delete control word at offset
    control_words[offset] = control_words[plastic_synapse - 1];
    control_words[plastic_synapse - 1] = 0;

    // Decrement FP
    fixed_region->num_plastic--;
    return true;
}

bool synapse_dynamics_add_neuron(uint32_t id, synaptic_row_t row,
        weight_t weight, uint32_t delay, uint32_t type) {
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);
    synapse_row_plastic_data_t *plastic_data = synapse_row_plastic_region(row);
    plastic_synapse_t *plastic_words = plastic_data->synapses;
    plastic_synapse_t new_weight = synapse_structure_create_synapse(weight);
    control_t new_control = control_conversion(id, delay, type);

    control_t *control_words = synapse_row_plastic_controls(fixed_region);
    int32_t plastic_synapse = synapse_row_num_plastic_controls(fixed_region);

    // Add weight at offset
    plastic_words[plastic_synapse] = new_weight;

    // Add control word at offset
    control_words[plastic_synapse] = new_control;

    // Increment FP
    fixed_region->num_plastic++;
    return true;
}
