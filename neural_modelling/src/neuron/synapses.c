/*
 * Copyright (c) 2014 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Implementation of non-inlined API in synapses.h
#include "synapses.h"
#include "spike_processing.h"
#include "neuron.h"
#include "plasticity/synapse_dynamics.h"
#include <profiler.h>
#include <debug.h>
#include <spin1_api.h>
#include <utils.h>

//! if using profiler import profiler tags
#ifdef PROFILER_ENABLED
#include "profile_tags.h"
#endif //PROFILER_ENABLED

//! Globals required for synapse benchmarking to work.
uint32_t  num_fixed_pre_synaptic_events = 0;

//! The number of neurons
static uint32_t n_neurons;

//! The number of synapse types
static uint32_t n_synapse_types;

//! Ring buffers to handle delays between synapses and neurons
static weight_t *ring_buffers;

//! Ring buffer size
static uint32_t ring_buffer_size;

//! Ring buffer mask
static uint32_t ring_buffer_mask;

//! Amount to left shift the ring buffer by to make it an input
static uint32_t *ring_buffer_to_input_left_shifts;

//! \brief Number of bits needed for the synapse type and index
//! \details
//! ```
//! synapse_index_bits + synapse_type_bits
//! ```
uint32_t synapse_type_index_bits;
//! \brief Mask to pick out the synapse type and index.
//! \details
//! ```
//! synapse_index_mask | synapse_type_mask
//! ```
uint32_t synapse_type_index_mask;
//! Number of bits in the synapse index
uint32_t synapse_index_bits;
//! Mask to pick out the synapse index.
uint32_t synapse_index_mask;
//! Number of bits in the synapse type
uint32_t synapse_type_bits;
//! Mask to pick out the synapse type.
uint32_t synapse_type_mask;
//! Number of bits in the delay
uint32_t synapse_delay_bits;
//! Mask to pick out the delay
uint32_t synapse_delay_mask;

//! Count of the number of times the ring buffers have saturated
uint32_t synapses_saturation_count = 0;

//! Count of the synapses that have been skipped because the delay wasn't
//! big enough given how long the spike took to arrive
uint32_t skipped_synapses = 0;

//! Count of the spikes that are received late
uint32_t late_spikes = 0;

//! The maximum lateness of a spike
uint32_t max_late_spike = 0;

//! Number of neurons
static uint32_t n_neurons_peak;

//! The mask of the delay shifted into position i.e. pre-shift
static uint32_t synapse_delay_mask_shifted = 0;


/* PRIVATE FUNCTIONS */

#if LOG_LEVEL >= LOG_DEBUG
//! \brief get the synapse type character
//! \param[in] synapse_type: the synapse type
//! \return a single character string describing the synapse type
static inline const char *get_type_char(uint32_t synapse_type) {
    return neuron_get_synapse_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG

//! \brief Print a synaptic row.
//!
//! Only does anything when debugging.
//! \param[in] synaptic_row: The synaptic row to print
static inline void print_synaptic_row(synaptic_row_t synaptic_row) {
    log_debug("Synaptic row, at address %08x, Num plastic words:%u",
            (uint32_t) synaptic_row, synapse_row_plastic_size(synaptic_row));
    if (synaptic_row == NULL) {
        return;
    }
#if LOG_LEVEL >= LOG_DEBUG
    io_printf(IO_BUF, "----------------------------------------\n");

    // Get details of fixed region
    synapse_row_fixed_part_t *fixed_region =
            synapse_row_fixed_region(synaptic_row);
    address_t fixed_synapses = synapse_row_fixed_weight_controls(fixed_region);
    size_t n_fixed_synapses = synapse_row_num_fixed_synapses(fixed_region);
    io_printf(IO_BUF,
            "Fixed region %u fixed synapses (%u plastic control words):\n",
            n_fixed_synapses, synapse_row_num_plastic_controls(fixed_region));

    for (uint32_t i = 0; i < n_fixed_synapses; i++) {
        uint32_t synapse = fixed_synapses[i];
        uint32_t synapse_type = synapse_row_sparse_type(
                synapse, synapse_index_bits, synapse_type_mask);

        io_printf(IO_BUF, "%08x [%3d: (w: %5u (=",
                synapse, i, synapse_row_sparse_weight(synapse));
        synapses_print_weight(synapse_row_sparse_weight(synapse),
                ring_buffer_to_input_left_shifts[synapse_type]);
        io_printf(IO_BUF, "nA) d: %2u, %d, n = %3u)] - {%08x %08x}\n",
                synapse_row_sparse_delay(synapse, synapse_type_index_bits,
                        synapse_delay_mask),
                synapse_type,
                synapse_row_sparse_index(synapse, synapse_index_mask),
                synapse_delay_mask, synapse_type_index_bits);
    }

    // If there's a plastic region
    if (synapse_row_plastic_size(synaptic_row) > 0) {
        io_printf(IO_BUF, "----------------------------------------\n");
        synapse_row_plastic_data_t *plastic_data =
                synapse_row_plastic_region(synaptic_row);
        synapse_dynamics_print_plastic_synapses(
                plastic_data, fixed_region, ring_buffer_to_input_left_shifts);
    }

    io_printf(IO_BUF, "----------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! \brief Print the contents of the ring buffers.
//! \details Only does anything when debugging.
//! \param[in] time: The current timestamp
static inline void print_ring_buffers(uint32_t time) {
    log_debug("Ring Buffer at %u", time);
#if LOG_LEVEL >= LOG_DEBUG
    io_printf(IO_BUF, "----------------------------------------\n");
    uint32_t n_delay_bits = (1 << synapse_delay_bits);
    for (uint32_t n = 0; n < n_neurons; n++) {
        for (uint32_t t = 0; t < n_synapse_types; t++) {
            // Determine if this row can be omitted
            for (uint32_t d = 0; d < n_delay_bits; d++) {
                if (ring_buffers[synapse_row_get_ring_buffer_index(
                        d + time, t, n, synapse_type_index_bits,
                        synapse_index_bits, synapse_delay_mask)] != 0) {
                    goto doPrint;
                }
            }
            continue;
        doPrint:
            // Have to print the row
            io_printf(IO_BUF, "%3d(%s):", n, get_type_char(t));
            for (uint32_t d = 0; d < n_delay_bits; d++) {
                io_printf(IO_BUF, " ");
                uint32_t ring_buffer_index = synapse_row_get_ring_buffer_index(
                        d + time, t, n, synapse_type_index_bits,
                        synapse_index_bits, synapse_delay_mask);
                synapses_print_weight(ring_buffers[ring_buffer_index],
                        ring_buffer_to_input_left_shifts[t]);
            }
            io_printf(IO_BUF, "\n");
        }
    }
    io_printf(IO_BUF, "----------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}


//! \brief The "inner loop" of the neural simulation.
//! \details Every spike event could cause up to 256 different weights to
//!     be put into the ring buffer.
//! \param[in] fixed_region: The fixed region of the synaptic matrix
//! \param[in] time: The current simulation time
//! \return Always true
static inline bool process_fixed_synapses(
        synapse_row_fixed_part_t *fixed_region, uint32_t time,
        uint32_t colour_delay) {
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(fixed_region);
    uint32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);

    num_fixed_pre_synaptic_events += fixed_synapse;

    // Pre-mask the time and account for colour delay
    uint32_t colour_delay_shifted = colour_delay << synapse_type_index_bits;
    uint32_t masked_time = ((time - colour_delay) & synapse_delay_mask) << synapse_type_index_bits;

    for (; fixed_synapse > 0; fixed_synapse--) {
        // Get the next 32 bit word from the synaptic_row
        // (should auto increment pointer in single instruction)
        uint32_t synaptic_word = *synaptic_words++;

        // If the (shifted) delay is non zero and too small, skip
        if (((synaptic_word & synapse_delay_mask_shifted) != 0) &&
        		((synaptic_word & synapse_delay_mask_shifted) <= colour_delay_shifted)) {
            skipped_synapses++;
            continue;
        }

        // The ring buffer index can be found by adding on the time to the delay
        // in the synaptic word directly, and then masking off the whole index.
        // The addition of the masked time to the delay even with the mask might
        // overflow into the weight at worst but can't affect the lower bits.
        uint32_t ring_buffer_index = (synaptic_word + masked_time) & ring_buffer_mask;
        uint32_t weight = synapse_row_sparse_weight(synaptic_word);

        // Add weight to current ring buffer value
        uint32_t accumulation = ring_buffers[ring_buffer_index] + weight;

        // If 17th bit is set, saturate accumulator at UINT16_MAX (0xFFFF)
        // **NOTE** 0x10000 can be expressed as an ARM literal,
        //          but 0xFFFF cannot.  Therefore, we use (0x10000 - 1)
        //          to obtain this value
        uint32_t sat_test = accumulation & 0x10000;
        if (sat_test) {
            accumulation = sat_test - 1;
            synapses_saturation_count++;
        }

        // Store saturated value back in ring-buffer
        ring_buffers[ring_buffer_index] = accumulation;
    }
    return true;
}

//! The layout of the synapse parameters region
struct synapse_params {
    uint32_t n_neurons;
    uint32_t n_synapse_types;
    uint32_t log_n_neurons;
    uint32_t log_n_synapse_types;
    uint32_t log_max_delay;
    uint32_t drop_late_packets;
    uint32_t incoming_spike_buffer_size;
    uint32_t ring_buffer_shifts[];
};

/* INTERFACE FUNCTIONS */
bool synapses_initialise(
        address_t synapse_params_address,
        uint32_t *n_neurons_out, uint32_t *n_synapse_types_out,
        weight_t **ring_buffers_out,
        uint32_t **ring_buffer_to_input_buffer_left_shifts,
        bool* clear_input_buffers_of_late_packets_init,
        uint32_t *incoming_spike_buffer_size) {
    struct synapse_params *params = (struct synapse_params *) synapse_params_address;
    *clear_input_buffers_of_late_packets_init = params->drop_late_packets;
    *incoming_spike_buffer_size = params->incoming_spike_buffer_size;
    n_neurons = params->n_neurons;
    *n_neurons_out = n_neurons;
    n_synapse_types = params->n_synapse_types;
    *n_synapse_types_out = n_synapse_types;

    uint32_t log_n_neurons = params->log_n_neurons;
    uint32_t log_n_synapse_types = params->log_n_synapse_types;
    uint32_t log_max_delay = params->log_max_delay;

    // Set up ring buffer left shifts
    ring_buffer_to_input_left_shifts =
            spin1_malloc(n_synapse_types * sizeof(uint32_t));
    if (ring_buffer_to_input_left_shifts == NULL) {
        log_error("Not enough memory to allocate ring buffer");
        return false;
    }

    // read in ring buffer to input left shifts
    spin1_memcpy(
            ring_buffer_to_input_left_shifts, params->ring_buffer_shifts,
            n_synapse_types * sizeof(uint32_t));
    *ring_buffer_to_input_buffer_left_shifts =
            ring_buffer_to_input_left_shifts;

    synapse_type_index_bits = log_n_neurons + log_n_synapse_types;
    synapse_type_index_mask = (1 << synapse_type_index_bits) - 1;
    synapse_index_bits = log_n_neurons;
    synapse_index_mask = (1 << synapse_index_bits) - 1;
    synapse_type_bits = log_n_synapse_types;
    synapse_type_mask = (1 << log_n_synapse_types) - 1;
    synapse_delay_bits = log_max_delay;
    synapse_delay_mask = (1 << synapse_delay_bits) - 1;
    synapse_delay_mask_shifted = synapse_delay_mask << synapse_type_index_bits;

    n_neurons_peak = 1 << log_n_neurons;

    uint32_t n_ring_buffer_bits =
            log_n_neurons + log_n_synapse_types + synapse_delay_bits;
    ring_buffer_size = 1 << (n_ring_buffer_bits);
    ring_buffer_mask = ring_buffer_size - 1;

    ring_buffers = spin1_malloc(ring_buffer_size * sizeof(weight_t));
    if (ring_buffers == NULL) {
        log_error("Could not allocate %u entries for ring buffers; Biggest space %u",
                ring_buffer_size, sark_heap_max(sark.heap, 0));
        return false;
    }
    for (uint32_t i = 0; i < ring_buffer_size; i++) {
        ring_buffers[i] = 0;
    }
    *ring_buffers_out = ring_buffers;

    log_info("Ready to process synapses for %u neurons with %u synapse types",
            n_neurons, n_synapse_types);

    return true;
}

void synapses_flush_ring_buffers(timer_t time) {
    uint32_t synapse_index = 0;
    uint32_t ring_buffer_index = synapse_row_get_first_ring_buffer_index(
            time, synapse_type_index_bits, synapse_delay_mask);;
    for (uint32_t s_i = n_synapse_types; s_i > 0; s_i--) {
        uint32_t neuron_index = 0;
        for (uint32_t n_i = n_neurons_peak; n_i > 0; n_i--) {
            ring_buffers[ring_buffer_index] = 0;
            ring_buffer_index++;
            neuron_index++;
        }
        synapse_index++;
    }
}

bool synapses_process_synaptic_row(
        uint32_t time, uint32_t spike_colour, uint32_t colour_mask,
		synaptic_row_t row, bool *write_back) {

    // Work out how much delay takes off or adds on to the actual delay because
    // of a delayed spike arrival time, or delayed change of time step in the
    // current core.  Spikes can be as late as the bits in colour_mask dictates.
	// Masked difference is used to calculate this, which will always be
	// positive because the mask removes the negative bit.
	// Example: time colour 8, spike colour 13, colour mask 0xF means time
	// colour has gone up to 15 and then wrapped since spike was sent.
    // 8 - 13 = -5; -5 & 0xF = 11, so spike was sent 11 steps ago.
    uint32_t time_colour = time & colour_mask;
    int32_t colour_diff = time_colour - spike_colour;
    uint32_t colour_delay = colour_diff & colour_mask;

    late_spikes += colour_delay & 0x1;
    if (colour_delay > max_late_spike) {
        max_late_spike = colour_delay;
    }

    // By default don't write back
    *write_back = false;

    // Get address of non-plastic region from row
    synapse_row_fixed_part_t *fixed_region = synapse_row_fixed_region(row);

    // **TODO** multiple optimised synaptic row formats
    //if (plastic_tag(row) == 0) {
    // If this row has a plastic region
    if (synapse_row_plastic_size(row) > 0) {
        // Get region's address
        synapse_row_plastic_data_t *plastic_data =
                synapse_row_plastic_region(row);

        // Process any plastic synapses
        profiler_write_entry_disable_fiq(
                PROFILER_ENTER | PROFILER_PROCESS_PLASTIC_SYNAPSES);
        if (!synapse_dynamics_process_plastic_synapses(plastic_data,
                fixed_region, ring_buffers, time, colour_delay, write_back)) {
            return false;
        }
        profiler_write_entry_disable_fiq(
                PROFILER_EXIT | PROFILER_PROCESS_PLASTIC_SYNAPSES);
    }

    // Process any fixed synapses
    // **NOTE** this is done after initiating DMA in an attempt
    // to hide cost of DMA behind this loop to improve the chance
    // that the DMA controller is ready to read next synaptic row afterwards
    return process_fixed_synapses(fixed_region, time, colour_delay);
    //}
}

uint32_t synapses_get_pre_synaptic_events(void) {
    return (num_fixed_pre_synaptic_events +
            synapse_dynamics_get_plastic_pre_synaptic_events());
}

void synapses_resume(timer_t time) {
    // If the time has been reset to zero then the ring buffers need to be
    // flushed in case there is a delayed spike left over from a previous run
    if (time == 0) {
        for (uint32_t i = 0; i < ring_buffer_size; i++) {
            ring_buffers[i] = 0;
        }
    }
}
