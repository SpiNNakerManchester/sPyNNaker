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
//! \brief Implementation of delay extensions

#include "delay_extension.h"

#include <common/neuron-typedefs.h>
#include <common/in_spikes.h>
#include <bit_field.h>
#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <spin1_api.h>
#include <common/send_mc.h>

//! the size of the circular queue for packets.
#define IN_BUFFER_SIZE 256

//! the point where the count has saturated.
#define COUNTER_SATURATION_VALUE 255

//! values for the priority for each callback
enum delay_extension_callback_priorities {
    MC_PACKET = -1, //!< multicast packet reception uses FIQ
    TIMER = 0,      //!< Call timer at 0 to keep it quick
    USER = 0,       //!< Call user at 0 as well; will be behind timer
    SDP = 1,        //!< SDP handling is queued
    BACKGROUND = 1, //!< Background processing
    DMA = 2         //!< DMA is not actually used
};

//! Structure of the provenance data
struct delay_extension_provenance {
    //! Number of input spikes
    uint32_t n_packets_received;
    //! Number of spikes transferred via queue
    uint32_t n_packets_processed;
    //! Number of spikes added to delay processing
    uint32_t n_packets_added;
    //! Number of spikes sent
    uint32_t n_packets_sent;
    //! Number of circular buffer overflows (spikes internally dropped)
    uint32_t n_buffer_overflows;
    //! Number of times we had to back off because the comms hardware was busy
    uint32_t n_delays;
    //! number of times the TDMA fell behind its slot
    uint32_t times_tdma_fell_behind;
    //! number of packets lost due to count saturation of uint8
    uint32_t n_packets_lost_due_to_count_saturation;
    //! number of packets dropped due to invalid neuron value
    uint32_t n_packets_dropped_due_to_invalid_neuron_value;
    //! number of packets dropped due to invalid key
    uint32_t n_packets_dropped_due_to_invalid_key;
    //! number of packets dropped due to out of time
    uint32_t count_input_buffer_packets_late;
    //! Maximum backgrounds queued
    uint32_t max_backgrounds_queued;
    //! Background queue overloads
    uint32_t n_background_queue_overloads;
};

// Globals
//! bool in int form for if there is a key
static bool has_key;
//! Base multicast key for sending messages
static uint32_t key = 0;
//! Key for receiving messages
static uint32_t incoming_key = 0;
//! Mask for ::incoming_key to say which messages are for this program
static uint32_t incoming_mask = 0;
//! \brief Mask for key (that matches ::incoming_key/::incoming_mask) to extract
//! the neuron ID from it
static uint32_t incoming_neuron_mask = 0;

//! Number of neurons supported.
static uint32_t num_neurons = 0;

//! number of possible keys.
static uint32_t max_keys = 0;

//! Whether to clear packets each timestep
static bool clear_input_buffers_of_late_packets;

//! Simulation time
static uint32_t time = UINT32_MAX;
//! Simulation speed
static uint32_t simulation_ticks = 0;
//! True if we're running forever
static uint32_t infinite_run;

//! \brief The spike counters, as a 2D array
//! ```
//! spike_counters[time_slot][neuron_id]
//! ```
//! Time slots are the time of reception of the spike, masked by
//! ::num_delay_slots_mask, and neuron IDs are extracted from the spike key by
//! masking with ::incoming_neuron_mask
static uint8_t **spike_counters = NULL;
//! The number of delay stages.
static uint32_t num_delay_stages = 0;
//! The number of delays within a delay stage
static uint32_t n_delay_in_a_stage = 0;
//! The total number of delay slots
static uint32_t num_delay_slots = 0;
//! Mask for converting time into the current delay slot
static uint32_t num_delay_slots_mask = 0;
//! Size of each bitfield in ::neuron_delay_stage_config
static uint32_t neuron_bit_field_words = 0;

//! Number of input spikes
static uint32_t n_in_spikes = 0;
//! Number of spikes transferred via queue
static uint32_t n_processed_spikes = 0;
//! Number of spikes sent
static uint32_t n_spikes_sent = 0;
//! Number of spikes added to delay processing
static uint32_t n_spikes_added = 0;

//! Number of times we had to back off because the comms hardware was busy
static uint32_t n_delays = 0;

//! Number of packets dropped due to count saturation
static uint32_t saturation_count = 0;

//! number of packets dropped due to invalid neuron id
static uint32_t n_packets_dropped_due_to_invalid_neuron_value = 0;

//! number of packets dropped due to invalid key
static uint32_t n_packets_dropped_due_to_invalid_key = 0;

//! number of packets late
static uint32_t count_input_buffer_packets_late;

//! Used for configuring the timer hardware
static uint32_t timer_period = 0;

//! Is spike processing happening right now?
static bool spike_processing = false;

//! The number of background tasks queued / running
static uint32_t n_backgrounds_queued = 0;

//! The number of times the background couldn't be added
static uint32_t n_background_overloads = 0;

//! The maximum number of background tasks queued
static uint32_t max_backgrounds_queued = 0;

//! The number of colour bits (both from source and to send)
static uint32_t n_colour_bits = 0;

//! The mask to apply to get the colour from the current timestep or key
static uint32_t colour_mask = 0;

//! The colour for the current time step
static uint32_t colour = 0;

//---------------------------------------
// Because we don't want to include string.h or strings.h for memset
//! \brief Sets an array of counters to zero
//!
//! This is basically just bzero()
//!
//! \param[out] counters: The array to zero
//! \param[in] num_items: The size of the array
static inline void zero_spike_counters(
        uint8_t *counters, uint32_t num_items) {
    for (uint32_t i = 0 ; i < num_items ; i++) {
        counters[i] = 0;
    }
}

//! \brief Rounds up to the next power of two
//! \param[in] v: The value to round up
//! \return The minimum power of two that is no smaller than the argument
static inline uint32_t round_to_next_pot(uint32_t v) {
    v--;
    v |= v >> 1;
    v |= v >> 2;
    v |= v >> 4;
    v |= v >> 8;
    v |= v >> 16;
    v++;
    return v;
}

//! \brief Read the configuration region.
//! \param[in] params: The configuration region.
//! \return True if successful
static bool read_parameters(struct delay_parameters *params) {
    log_debug("read_parameters: starting");

    has_key = params->has_key;
    key = params->key;
    incoming_key = params->incoming_key;
    incoming_mask = params->incoming_mask;
    incoming_neuron_mask = ~incoming_mask;
    log_debug("\t key = 0x%08x, incoming key = 0x%08x, incoming mask = 0x%08x,"
            "incoming key mask = 0x%08x",
            key, incoming_key, incoming_mask, incoming_neuron_mask);

    num_neurons = params->n_atoms;
    neuron_bit_field_words = get_bit_field_size(num_neurons);

    num_delay_stages = params->n_delay_stages;
    n_delay_in_a_stage = params->n_delay_in_a_stage;
    max_keys = num_neurons * num_delay_stages;

    clear_input_buffers_of_late_packets = params->clear_packets;

    num_delay_slots = num_delay_stages * n_delay_in_a_stage;
    // We need an extra slot here (to make one clearable after the maximum delay
    // time), and a power of 2 (to make it easier to loop)
    uint32_t num_delay_slots_pot = round_to_next_pot(num_delay_slots + 1);
    num_delay_slots_mask = num_delay_slots_pot - 1;

    log_info("\t parrot neurons = %u, neuron bit field words = %u,"
            " num delay stages = %u, num delay slots = %u (pot = %u),"
            " num delay slots mask = %08x, n delay in a stage = %u",
            num_neurons, neuron_bit_field_words,
            num_delay_stages, num_delay_slots, num_delay_slots_pot,
            num_delay_slots_mask, n_delay_in_a_stage);

    // Allocate array of counters for each delay slot
    spike_counters = spin1_malloc(num_delay_slots_pot * sizeof(uint8_t*));
    if (spike_counters == NULL) {
        log_error("failed to allocate memory for array of size %u bytes",
                num_delay_slots_pot * sizeof(uint8_t*));
        return false;
    }

    for (uint32_t s = 0; s < num_delay_slots_pot; s++) {
        // Allocate an array of counters for each neuron and zero
        spike_counters[s] = spin1_malloc(num_neurons * sizeof(uint8_t));
        if (spike_counters[s] == NULL) {
            log_error("failed to allocate memory for bitfield of size %u bytes",
                    num_neurons * sizeof(uint8_t));
            return false;
        }
        zero_spike_counters(spike_counters[s], num_neurons);
    }

    n_colour_bits = params->n_colour_bits;
    colour_mask = (1 << n_colour_bits) - 1;

    log_debug("read_parameters: completed successfully");
    return true;
}

//! \brief Writes the provenance data
//! \param[out] provenance_region: Where to write the provenance
static void store_provenance_data(address_t provenance_region) {
    log_debug("writing other provenance data");
    struct delay_extension_provenance *prov = (void *) provenance_region;

    // store the data into the provenance data region
    prov->n_packets_received = n_in_spikes;
    prov->n_packets_processed = n_processed_spikes;
    prov->n_packets_added = n_spikes_added;
    prov->n_packets_sent = n_spikes_sent;
    prov->n_buffer_overflows = in_spikes_get_n_buffer_overflows();
    prov->n_delays = n_delays;
    prov->times_tdma_fell_behind = 0;
    prov->n_packets_lost_due_to_count_saturation = saturation_count;
    prov->n_packets_dropped_due_to_invalid_neuron_value =
        n_packets_dropped_due_to_invalid_neuron_value;
    prov->n_packets_dropped_due_to_invalid_key =
        n_packets_dropped_due_to_invalid_key;
    prov->count_input_buffer_packets_late = count_input_buffer_packets_late;
    prov->n_background_queue_overloads = n_background_overloads;
    prov->max_backgrounds_queued = max_backgrounds_queued;
    log_debug("finished other provenance data");
}

//! \brief Read the application configuration
//! \return True if initialisation succeeded.
static bool initialize(void) {
    log_info("initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(ds_regions)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM, ds_regions),
            APPLICATION_NAME_HASH, &timer_period, &simulation_ticks,
            &infinite_run, &time, SDP, DMA)) {
        return false;
    }

    // set provenance function
    simulation_set_provenance_function(
            store_provenance_data,
            data_specification_get_region(PROVENANCE_REGION, ds_regions));

    // Get the parameters
    if (!read_parameters(data_specification_get_region(
            DELAY_PARAMS, ds_regions))) {
        return false;
    }

    log_info("initialise: completed successfully");

    return true;
}

// Callbacks
//! \brief Handles incoming spikes (FIQ)
//!
//! Adds the spikes to the circular buffer handling spikes for later handling by
//! ::spike_process()
//!
//! \param[in] key: the key of the multicast message
//! \param payload: ignored
static void incoming_spike_callback(uint key, uint payload) {

    if (payload == 0) {
        payload = 1;
    }
    log_debug("Received spike %x", key);

    for (uint32_t i = payload; i > 0; i--) {
        n_in_spikes++;
        in_spikes_add_spike(key);
    }

    if (!spike_processing) {
        if (spin1_trigger_user_event(0, 0)) {
            spike_processing = true;
        }
    }
}

//! \brief Gets the neuron ID of the incoming spike
//! \param[in] k: The key
//! \return the neuron ID
static inline index_t key_n(key_t k) {
    return k & incoming_neuron_mask;
}

//! \brief Processes spikes queued by ::incoming_spike_callback()
static inline void spike_process(void) {



    // While there are any incoming spikes
    spike_t s;
    uint32_t state = spin1_int_disable();
    while (in_spikes_get_next_spike(&s)) {
        spin1_mode_restore(state);
        n_processed_spikes++;

        if ((s & incoming_mask) == incoming_key) {
            // Mask out neuron ID
            uint32_t spike_id = key_n(s);
            uint32_t spike_colour = spike_id & colour_mask;
            uint32_t neuron_id = spike_id >> n_colour_bits;
            if (neuron_id < num_neurons) {

            	// Account for delayed spikes
            	int32_t colour_diff = colour - spike_colour;
            	uint32_t colour_delay = colour_diff & colour_mask;

            	// Get current time slot of incoming spike counters
				uint32_t time_slot = (time + colour_delay) & num_delay_slots_mask;
				uint8_t *time_slot_spike_counters = spike_counters[time_slot];

                // Increment counter
                if (time_slot_spike_counters[neuron_id] ==
                        COUNTER_SATURATION_VALUE) {
                    saturation_count += 1;
                } else {
                	time_slot_spike_counters[neuron_id]++;
                }
                log_debug("Incrementing counter %u = %u\n",
                        neuron_id,
						time_slot_spike_counters[neuron_id]);
                n_spikes_added++;
            } else {
                n_packets_dropped_due_to_invalid_neuron_value += 1;
                log_debug("Invalid neuron ID %u", neuron_id);
            }
        } else {
            n_packets_dropped_due_to_invalid_key += 1;
            log_debug("Invalid spike key 0x%08x", s);
        }
        state = spin1_int_disable();
    }

    spike_processing = false;
    spin1_mode_restore(state);
}

//! \brief User event callback.
//! \details Delegates to spike_process()
//! \param[in] unused0: unused
//! \param[in] unused1: unused
static void user_callback(UNUSED uint unused0, UNUSED uint unused1) {
    spike_process();
}

//! \brief Background event callback.
//! \details Handles sending delayed spikes at the right time.
//! \param[in] local_time: current simulation time
//! \param[in] timer_count: unused
static void background_callback(uint local_time, UNUSED uint timer_count) {
    // Loop through delay stages
    for (uint32_t d = 0; d < num_delay_stages; d++) {
        uint32_t delay_stage_delay = (d + 1) * n_delay_in_a_stage;
        if (local_time >= delay_stage_delay) {
            uint32_t delay_stage_time_slot =
                    (local_time - delay_stage_delay) & num_delay_slots_mask;
            uint8_t *delay_stage_spike_counters =
                    spike_counters[delay_stage_time_slot];

            log_debug("%u: Checking time slot %u for delay stage %u (delay %u)",
                    local_time, delay_stage_time_slot, d, delay_stage_delay);

            // Loop through neurons
            for (uint32_t n = 0; n < num_neurons; n++) {

                // If no spikes to send, skip
                if (delay_stage_spike_counters[n] == 0) {
                    continue;
                }

                // Calculate key all spikes coming from this neuron will be
                // sent with
                uint32_t neuron_index = ((d * num_neurons) + n);
                uint32_t neuron_key = neuron_index + key;
                uint32_t spike_key = (neuron_key << n_colour_bits) | colour;

                log_debug("Neuron %u sending %u spikes after delay"
                        "stage %u with key %x",
                        n, delay_stage_spike_counters[n], d,
                        spike_key);

                // fire n spikes as payload, 1 as none payload.
                if (has_key) {
                    if (delay_stage_spike_counters[n] > 1) {
                        log_debug(
                            "%d: sending packet with key 0x%08x and payload %d",
                            time, spike_key, delay_stage_spike_counters[n]);

                        send_spike_mc_payload(spike_key, delay_stage_spike_counters[n]);

                        // update counter
                        n_spikes_sent += delay_stage_spike_counters[n];
                    } else if (delay_stage_spike_counters[n] == 1) {
                        log_debug("%d: sending spike with key 0x%08x", time, spike_key);

                        send_spike_mc(spike_key);

                        // update counter
                        n_spikes_sent++;
                    }
                }
            }
        }
    }
    n_backgrounds_queued--;
}

//! \brief Main timer callback
//! \param[in] timer_count: The current time
//! \param unused1: unused
static void timer_callback(uint timer_count, UNUSED uint unused1) {
    uint32_t state = spin1_int_disable();
    uint32_t n_spikes = in_spikes_size();
    if (clear_input_buffers_of_late_packets) {
        in_spikes_clear();
    }
    // Record the count whether clearing or not for provenance
    count_input_buffer_packets_late += n_spikes;
    time++;

    // Clear counters
    if (time > num_delay_slots) {
        uint32_t clearable_slot = ((time - 1) - num_delay_slots) & num_delay_slots_mask;
        log_debug("%d: Clearing time slot %d", time, clearable_slot);
        zero_spike_counters(spike_counters[clearable_slot], num_neurons);
    }

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (simulation_is_finished()) {
        // handle the pause and resume functionality
        simulation_handle_pause_resume(NULL);

        log_debug("Delay extension finished at time %u, %u received spikes, "
                "%u processed spikes, %u sent spikes, %u added spikes",
                time, n_in_spikes, n_processed_spikes, n_spikes_sent,
                n_spikes_added);

        log_debug("Delayed %u times", n_delays);

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;

        simulation_ready_to_read();
        spin1_mode_restore(state);
        return;
    }

    // Set the colour for the time step
    colour = time & colour_mask;

    if (!spin1_schedule_callback(background_callback, time, timer_count, BACKGROUND)) {
        // We have failed to do this timer tick!
        n_background_overloads++;
    } else {
        n_backgrounds_queued++;
        if (n_backgrounds_queued > max_backgrounds_queued) {
            max_backgrounds_queued++;
        }
    }
    spin1_mode_restore(state);
}

//! Entry point
void c_main(void) {
    log_info("max dtcm supply %d", sark_heap_max(sark.heap, 0));
    if (!initialize()) {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Initialise the incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(IN_BUFFER_SIZE)) {
        rt_error(RTE_SWERR);
    }

    // Set timer tick (in microseconds)
    log_debug("Timer period %u", timer_period);
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(MC_PACKET_RECEIVED, incoming_spike_callback, MC_PACKET);
    spin1_callback_on(MCPL_PACKET_RECEIVED, incoming_spike_callback, MC_PACKET);
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);
    spin1_callback_on(USER_EVENT, user_callback, USER);

    simulation_run();
}
