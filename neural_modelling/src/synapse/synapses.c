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

#include "synapses.h"
#include "spike_processing.h"
#include "neuron/neuron.h"
#include "synapse/plasticity/synapse_dynamics.h"
#include "spike_profiling.h"

#include <profiler.h>
#include <debug.h>
#include <spin1_api.h>
#include <utils.h>

#define DMA_TAG_WRITE_SYNAPTIC_CONTRIBUTION 1
#define SYNAPSE_RECORDING_INDEX 0

//! if using profiler import profiler tags
#ifdef PROFILER_ENABLED
    #include "profile_tags.h"
#endif



// Globals required for synapse benchmarking to work.
uint32_t num_fixed_pre_synaptic_events = 0;

uint32_t num_fixed_pre_synaptic_events_per_timestep = 0;
uint8_t zero_target_spikes_per_dt = 0;

extern uint32_t spikes_remaining_this_tick;
spike_holder_t syn_rec;
extern uint8_t kickstarts;

// The number of neurons
static uint32_t n_neurons;

// The number of synapse types implemented by this core
static uint32_t n_synapse_types;

// The index corresponding to the implemented synapse type
static uint8_t synapse_index;

// Ring buffers to handle delays between synapses and neurons
static weight_t *ring_buffers;

// Amount to left shift the ring buffer by to make it an input
static uint32_t *ring_buffer_to_input_left_shifts;

// Count of the number of times the ring buffers have saturated
static uint32_t saturation_count = 0;

static uint32_t synapse_type_index_bits;
static uint32_t synapse_type_index_mask;
static uint32_t synapse_index_bits;
static uint32_t synapse_index_mask;
static uint32_t synapse_type_bits;
static uint32_t synapse_type_mask;

static uint32_t memory_index;
static uint32_t offset;

static weight_t *synaptic_region;

// Size of the memory chunk containing this timestep's ring buffers
static size_t size_to_be_transferred;

// Recording
static uint32_t n_recorded_vars;

static uint32_t is_recording;

//! The number of timesteps between each variable recording
static uint32_t *var_recording_rate;

//! Count of timesteps until next variable recording
static uint32_t *var_recording_count;

//! Increment of count until next variable recording
//! - 0 if not recorded, 1 if recorded
static uint32_t *var_recording_increment;

//! The index to record each variable to for each neuron
static uint8_t *var_recording_indexes;

//! The values of the recorded variables
static timed_state_t **var_recording_values;

//! The size of the recorded variables in bytes for a timestep
static uint32_t *var_recording_size;

//! parameters that reside in the synapse_parameter_data_region in human
//! readable form
typedef enum parameters_in_synapse_parameter_data_region {
    N_NEURONS_TO_SIMULATE, N_SYNAPSE_TYPES, INCOMING_SPIKE_BUFFER_SIZE,
    SYNAPSE_INDEX, MEM_INDEX, OFFSET, N_RECORDED_VARIABLES,
    IS_RECORDING, START_OF_GLOBAL_PARAMETERS,
} parameters_in_synapse_parameter_data_region;


/* PRIVATE FUNCTIONS */

static inline void _print_synaptic_row(synaptic_row_t synaptic_row) {
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("Synaptic row, at address %08x Num plastic words:%u\n",
              (uint32_t )synaptic_row, synapse_row_plastic_size(synaptic_row));
    if (synaptic_row == NULL) {
        return;
    }
    log_debug("----------------------------------------\n");

    // Get details of fixed region
    address_t fixed_region_address = synapse_row_fixed_region(synaptic_row);
    address_t fixed_synapses = synapse_row_fixed_weight_controls(
        fixed_region_address);
    size_t n_fixed_synapses = synapse_row_num_fixed_synapses(
        fixed_region_address);
    log_debug("Fixed region %u fixed synapses (%u plastic control words):\n",
              n_fixed_synapses,
              synapse_row_num_plastic_controls(fixed_region_address));

    for (uint32_t i = 0; i < n_fixed_synapses; i++) {
        uint32_t synapse = fixed_synapses[i];
        uint32_t synapse_type = synapse_row_sparse_type(
            synapse, synapse_index_bits, synapse_type_mask);

        log_debug("%08x [%3d: (w: %5u (=", synapse, i,
                  synapse_row_sparse_weight(synapse));
        synapses_print_weight(synapse_row_sparse_weight(synapse),
                              ring_buffer_to_input_left_shifts[synapse_type]);
        log_debug(
            "nA) d: %2u, %s, n = %3u)] - {%08x %08x}\n",
            synapse_row_sparse_delay(synapse, synapse_type_index_bits),
            synapse_types_get_type_char(synapse_type),
            synapse_row_sparse_index(synapse, synapse_index_mask),
            SYNAPSE_DELAY_MASK, synapse_type_index_bits);
    }

    // If there's a plastic region
    if (synapse_row_plastic_size(synaptic_row) > 0) {
        log_debug("----------------------------------------\n");
        address_t plastic_region_address =
            synapse_row_plastic_region(synaptic_row);
        synapse_dynamics_print_plastic_synapses(
            plastic_region_address, fixed_region_address,
            ring_buffer_to_input_left_shifts);
    }

    log_debug("----------------------------------------\n");
#else
    use(synaptic_row);
#endif // LOG_LEVEL >= LOG_DEBUG
}

static inline void _print_ring_buffers(uint32_t time) {
#if LOG_LEVEL >= LOG_DEBUG
    io_printf(IO_BUF, "Ring Buffer at %u\n", time);
    io_printf(IO_BUF, "----------------------------------------\n");
    for (uint32_t n = 0; n < n_neurons; n++) {
        for (uint32_t t = 0; t < n_synapse_types; t++) {
            const char *type_string = synapse_types_get_type_char(t);
            bool empty = true;
            for (uint32_t d = 0; d < (1 << SYNAPSE_DELAY_BITS); d++) {
                empty = empty && (ring_buffers[
                    synapses_get_ring_buffer_index(d + time, t, n,
                       synapse_type_index_bits, synapse_index_bits)] == 0);
            }
            if (!empty) {
                io_printf(IO_BUF, "%3d(%s):", n, type_string);
                for (uint32_t d = 0; d < (1 << SYNAPSE_DELAY_BITS); d++) {
                    log_debug(" ");
                    uint32_t ring_buffer_index =
                        synapses_get_ring_buffer_index(d + time, t, n,
                           synapse_index_bits, synapse_index_bits);
                    synapses_print_weight(ring_buffers[ring_buffer_index],
                                          ring_buffer_to_input_left_shifts[t]);
                }
                io_printf(IO_BUF, "\n");
            }
        }
    }
    io_printf(IO_BUF, "----------------------------------------\n");
#else
    use(time);
#endif // LOG_LEVEL >= LOG_DEBUG
}

static inline void _print_inputs() {
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("Inputs\n");

    bool empty = true;
    for (index_t i = 0; i < n_neurons; i++) {
        empty = empty
                && (bitsk(synapse_types_get_excitatory_input(
                        &(neuron_synapse_shaping_params[i]))
                    - synapse_types_get_inhibitory_input(
                        &(neuron_synapse_shaping_params[i]))) == 0);
    }

    if (!empty) {
        log_debug("-------------------------------------\n");

        for (index_t i = 0; i < n_neurons; i++) {
            input_t input =
                synapse_types_get_excitatory_input(
                    &(neuron_synapse_shaping_params[i]))
                - synapse_types_get_inhibitory_input(
                    &(neuron_synapse_shaping_params[i]));
            if (bitsk(input) != 0) {
                log_debug("%3u: %12.6k (= ", i, input);
                synapse_types_print_input(
                    &(neuron_synapse_shaping_params[i]));
                log_debug(")\n");
            }
        }
        log_debug("-------------------------------------\n");
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}


// This is the "inner loop" of the neural simulation.
// Every spike event could cause up to 256 different weights to
// be put into the ring buffer.
static inline void _process_fixed_synapses(
        address_t fixed_region_address, uint32_t time) {
    register uint32_t *synaptic_words = synapse_row_fixed_weight_controls(
        fixed_region_address);
    register uint32_t fixed_synapse = synapse_row_num_fixed_synapses(
        fixed_region_address);

//    num_fixed_pre_synaptic_events += fixed_synapse;
    num_fixed_pre_synaptic_events += 1; // count processed spikes instead
    num_fixed_pre_synaptic_events_per_timestep++;

    if (!fixed_synapse){
    	// packet targets zero spikes
    	zero_target_spikes_per_dt++;
    } else {
    for (; fixed_synapse > 0; fixed_synapse--) {

        // Get the next 32 bit word from the synaptic_row
        // (should auto increment pointer in single instruction)
        uint32_t synaptic_word = *synaptic_words++;

        // Extract components from this word
        uint32_t delay = synapse_row_sparse_delay(synaptic_word,
            synapse_type_index_bits);
        uint32_t combined_synapse_neuron_index = synapse_row_sparse_type_index(
                synaptic_word, synapse_type_index_mask);
        uint32_t weight = synapse_row_sparse_weight(synaptic_word);

        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
            delay + time, combined_synapse_neuron_index,
            synapse_index_bits);

        // Add weight to current ring buffer value
        uint32_t accumulation = ring_buffers[ring_buffer_index] + weight;

        // If 17th bit is set, saturate accumulator at UINT16_MAX (0xFFFF)
        // **NOTE** 0x10000 can be expressed as an ARM literal,
        //          but 0xFFFF cannot.  Therefore, we use (0x10000 - 1)
        //          to obtain this value
        uint32_t sat_test = accumulation & 0x10000;
        if (sat_test) {
            accumulation = sat_test - 1;
            saturation_count += 1;
        }

        // Store saturated value back in ring-buffer

        ring_buffers[ring_buffer_index] = accumulation;
    }
    }
}

//! private method for doing output debug data on the synapses
static inline void _print_synapse_parameters() {
//! only if the models are compiled in debug mode will this method contain
//! said lines.
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------\n");
    for (index_t n = 0; n < n_neurons; n++) {
        synapse_types_print_parameters(&(neuron_synapse_shaping_params[n]));
    }
    log_debug("-------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}


/* INTERFACE FUNCTIONS */
bool synapses_initialise(
        address_t synapse_params_address, address_t direct_matrix_address,
        uint32_t *n_neurons_value, uint32_t *n_synapse_types_value,
        uint32_t *incoming_spike_buffer_size,
        uint32_t **ring_buffer_to_input_buffer_left_shifts,
        address_t *direct_synapses_address) {

    log_debug("synapses_initialise: starting");

    // Neuron details
    *n_neurons_value = synapse_params_address[N_NEURONS_TO_SIMULATE];
    n_neurons = *n_neurons_value;

    *n_synapse_types_value = synapse_params_address[N_SYNAPSE_TYPES];
    n_synapse_types = *n_synapse_types_value;

    // Read the size of the incoming spike buffer to use
    *incoming_spike_buffer_size = synapse_params_address[INCOMING_SPIKE_BUFFER_SIZE];

    synapse_index = synapse_params_address[SYNAPSE_INDEX];

    memory_index = synapse_params_address[MEM_INDEX];

    offset = synapse_params_address[OFFSET];

    n_recorded_vars = synapse_params_address[N_RECORDED_VARIABLES];

    is_recording = synapse_params_address[IS_RECORDING];

    // Set up ring buffer left shifts
    ring_buffer_to_input_left_shifts = (uint32_t *) spin1_malloc(
        n_synapse_types * sizeof(uint32_t));
    spin1_memcpy(
    ring_buffer_to_input_left_shifts, synapse_params_address + START_OF_GLOBAL_PARAMETERS,
        n_synapse_types * sizeof(uint32_t));
    *ring_buffer_to_input_buffer_left_shifts =
        ring_buffer_to_input_left_shifts;

    var_recording_rate = (uint32_t *) spin1_malloc(
        n_recorded_vars * sizeof(uint32_t));
    if (var_recording_rate == NULL) {
        log_error("Could not allocate space for var_recording_rate");
        return false;
    }
    var_recording_count = (uint32_t *) spin1_malloc(
        n_recorded_vars * sizeof(uint32_t));
    if (var_recording_count == NULL) {
        log_error("Could not allocate space for var_recording_count");
        return false;
    }
    var_recording_increment = (uint32_t *) spin1_malloc(
        n_recorded_vars * sizeof(uint32_t));
    if (var_recording_increment == NULL) {
        log_error("Could not allocate space for var_recording_increment");
        return false;
    }
    var_recording_indexes = (uint8_t *) spin1_malloc(
        n_recorded_vars * sizeof(uint8_t));
    if (var_recording_indexes == NULL) {
        log_error("Could not allocate space for var_recording_indexes");
        return false;
    }
    var_recording_size = (uint32_t *) spin1_malloc(
        n_recorded_vars * sizeof(uint32_t));
    if (var_recording_size == NULL) {
        log_error("Could not allocate space for var_recording_size");
        return false;
    }
    var_recording_values = (timed_state_t **) spin1_malloc(
        n_recorded_vars * sizeof(timed_state_t *));
    if (var_recording_values == NULL) {
        log_error("Could not allocate space for var_recording_values");
        return false;
    }

    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        var_recording_values[i] = (timed_state_t *) spin1_malloc(
            sizeof(uint32_t) + (sizeof(state_t)));
            if (var_recording_values[i] == NULL) {
            log_error(
                "Could not allocate space for var_recording_values[%d]", i);
            return false;
        }
    }

    uint32_t ptr = START_OF_GLOBAL_PARAMETERS + n_synapse_types;

//    uint32_t n_words_for_n_neurons = (n_neurons + 3) >> 2;
    uint32_t n_words_for_n_neurons = 1;

    // Load other variable recording details
    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        var_recording_rate[i] = synapse_params_address[ptr++];
        uint32_t n_neurons_recording_var = synapse_params_address[ptr++];
        var_recording_size[i] =
            (n_neurons_recording_var + 1) * sizeof(uint32_t);
//        spin1_memcpy(
//            var_recording_indexes[i], &synapse_params_address[ptr],
//            n_neurons * sizeof(uint8_t));
        var_recording_indexes[i] = synapse_params_address[ptr];
        ptr += n_words_for_n_neurons;
    }

    for (uint32_t i = 0; i < n_recorded_vars; i++) {
        if (var_recording_rate[i] == 0) {
            // Setting increment to zero means count will never equal rate
            var_recording_increment[i] = 0;
            // Count is not rate so does not record
            var_recording_count[i] = 1;
        } else {
            // Increase one each call so count gets to rate
            var_recording_increment[i] = 1;
            // Using rate here so that the zero time is recorded
            var_recording_count[i] = var_recording_rate[i];
        }
    }

    // Work out the positions of the direct and indirect synaptic matrices
    // and copy the direct matrix to DTCM
    uint32_t direct_matrix_size = direct_matrix_address[0];
    log_debug("Direct matrix malloc size is %d", direct_matrix_size);

    if (direct_matrix_size != 0) {
        *direct_synapses_address = (address_t)
            spin1_malloc(direct_matrix_size);

        if (*direct_synapses_address == NULL) {
            log_error("Not enough memory to allocate direct matrix");
            return false;
        }
        log_debug(
            "Copying %u bytes of direct synapses to 0x%08x",
            direct_matrix_size, *direct_synapses_address);
        spin1_memcpy(
            *direct_synapses_address, &(direct_matrix_address[1]),
            direct_matrix_size);
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

    uint32_t n_ring_buffer_bits =
        log_n_neurons + log_n_synapse_types + SYNAPSE_DELAY_BITS;
    uint32_t ring_buffer_size = 1 << (n_ring_buffer_bits);

    ring_buffers = (weight_t *) spin1_malloc(
        ring_buffer_size * sizeof(weight_t));
    if (ring_buffers == NULL) {
        log_error(
            "Could not allocate %u entries for ring buffers", ring_buffer_size);
        return false;
    }
    for (uint32_t i = 0; i < ring_buffer_size; i++) {
        ring_buffers[i] = 0;
    }

    size_to_be_transferred =
        (1 << (log_n_neurons + log_n_synapse_types)) * sizeof(weight_t);

    synapse_type_index_bits = log_n_neurons + 1;
    synapse_type_index_mask = (1 << synapse_type_index_bits) - 1;
    synapse_index_bits = log_n_neurons;
    synapse_index_mask = (1 << synapse_index_bits) - 1;
    synapse_type_bits = log_n_synapse_types;
    synapse_type_mask = (1 << log_n_synapse_types) - 1;

    log_debug("synapses_initialise: completed successfully");
    _print_synapse_parameters();

    return true;
}

static inline void write_recording(timer_t time) {

    // Write recording data. Doesn't use DMA, since the cb is NULL
    for(uint32_t i = 0; i < n_recorded_vars; i++) {
       uint32_t index = var_recording_indexes[i];

		syn_rec.spikes_a = num_fixed_pre_synaptic_events_per_timestep & 0xFF;
		syn_rec.spikes_b = spikes_remaining_this_tick & 0xFF;
		syn_rec.spikes_c = kickstarts;
		syn_rec.spikes_d = zero_target_spikes_per_dt;


       var_recording_values[i]->states[index] = spike_profiling_get_spike_holder_as_accum(syn_rec);

       if (var_recording_count[i] == var_recording_rate[i]) {
            var_recording_count[i] = 1;
            var_recording_values[i]->time = time;
            recording_record_and_notify(
            i, var_recording_values[i], var_recording_size[i], NULL);
       } else {
            var_recording_count[i] += var_recording_increment[i];
       }
    }
}

void synapses_do_timestep_update(timer_t time) {

    _print_ring_buffers(time);

    // Disable interrupts to stop DMAs interfering with the ring buffers
    //Interrupts are now disabled in the caller
    //uint32_t state = spin1_irq_disable();

    // Starting position of the memory chunk
    uint32_t ring_buffer_index = synapses_get_ring_buffer_index(
                time+1, 0, 0, synapse_index_bits,
                synapse_index_bits);

    // Start the transfer
    spin1_dma_transfer(
        DMA_TAG_WRITE_SYNAPTIC_CONTRIBUTION, synaptic_region, &ring_buffers[ring_buffer_index],
        DMA_WRITE, size_to_be_transferred);

    _print_inputs();

	if (is_recording) {
		write_recording(time);
		num_fixed_pre_synaptic_events_per_timestep = 0;
		kickstarts = 0;
		zero_target_spikes_per_dt = 0;
	}

    // Re-enable the interrupts
    //spin1_mode_restore(state);
}

bool synapses_process_synaptic_row(uint32_t time, synaptic_row_t row,
                                   bool write, uint32_t process_id) {

    _print_synaptic_row(row);

    // Get address of non-plastic region from row
    address_t fixed_region_address = synapse_row_fixed_region(row);

    // **TODO** multiple optimised synaptic row formats
    //if (plastic_tag(row) == 0)
    //{
    // If this row has a plastic region
    if (synapse_row_plastic_size(row) > 0) {

        // Get region's address
        address_t plastic_region_address = synapse_row_plastic_region(row);

        // Process any plastic synapses
        profiler_write_entry_disable_fiq(
            PROFILER_ENTER | PROFILER_PROCESS_PLASTIC_SYNAPSES);
        if (!synapse_dynamics_process_plastic_synapses(plastic_region_address,
                fixed_region_address, ring_buffers, time)) {
            return false;
        }
        profiler_write_entry_disable_fiq(
            PROFILER_EXIT | PROFILER_PROCESS_PLASTIC_SYNAPSES);


        // Perform DMA write back
        if (write) {
            spike_processing_finish_write(process_id);
        }
    }

    // Process any fixed synapses
    // **NOTE** this is done after initiating DMA in an attempt
    // to hide cost of DMA behind this loop to improve the chance
    // that the DMA controller is ready to read next synaptic row afterwards
    _process_fixed_synapses(fixed_region_address, time);
    //}
    return true;
}

//! \brief returns the number of times the synapses have saturated their
//!        weights.
//! \return the number of times the synapses have saturated.
uint32_t synapses_get_saturation_count() {
    return saturation_count;
}

//! \brief returns the counters for plastic and fixed pre synaptic events
//! based on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//! returns 0
//! \return the counter for plastic and fixed pre synaptic events or 0
uint32_t synapses_get_pre_synaptic_events() {
    return (num_fixed_pre_synaptic_events +
            synapse_dynamics_get_plastic_pre_synaptic_events());
}


//! \brief  Searches the synaptic row for the the connection with the
//!         specified post-synaptic ID
//! \param[in] id: the (core-local) ID of the neuron to search for in the
//! synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[out] sp_data: the address of a struct through which to return
//! weight, delay information
//! \return bool: was the search successful?
bool find_static_neuron_with_id(uint32_t id, address_t row,
                                structural_plasticity_data_t *sp_data){
    address_t fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(
        fixed_region);

    uint32_t weight, delay;
    bool found = false;

    // Loop through plastic synapses
    for (; fixed_synapse > 0; fixed_synapse--) {

        // Get next control word (auto incrementing)
        // Check if index is the one I'm looking for
        uint32_t synaptic_word = *synaptic_words++;
        weight = synapse_row_sparse_weight(synaptic_word);
        delay = synapse_row_sparse_delay(synaptic_word, synapse_type_index_bits);
        if (synapse_row_sparse_index(synaptic_word, synapse_index_mask)==id){
            found = true;
            break;
        }
    }

    // Making assumptions explicit
    assert( synapse_row_num_plastic_controls(fixed_region) == 0 );

    if (found){
        sp_data -> weight = weight;
        sp_data -> offset = synapse_row_num_fixed_synapses(fixed_region) -
            fixed_synapse;
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
bool remove_static_neuron_at_offset(uint32_t offset, address_t row){
    address_t fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(
        fixed_region);

   // Delete control word at offset (contains weight)
    synaptic_words[offset] = synaptic_words[fixed_synapse-1];

    // Decrement FF
    fixed_region[0] = fixed_region[0] - 1;
    return true;
}

//! packing all of the information into the required static control word
static inline uint32_t _fixed_synapse_convert(
        uint32_t id, uint32_t weight, uint32_t delay, uint32_t type){
    uint32_t new_synapse = weight << (32 - SYNAPSE_WEIGHT_BITS);
    new_synapse |= ((delay & ((1 << SYNAPSE_DELAY_BITS) - 1)) <<
            synapse_type_index_bits);
    new_synapse |= ((type & ((1 << synapse_type_bits) - 1)) <<
            synapse_index_bits);
    new_synapse |= (id & ((1 << synapse_type_index_bits) - 1));
    return new_synapse;
}

//! \brief  Add a static entry in the synaptic row
//! \param[in] id: the (core-local) ID of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return bool: was the addition successful?
bool add_static_neuron_with_id(uint32_t id, address_t row, uint32_t weight,
                               uint32_t delay, uint32_t type){
    address_t fixed_region = synapse_row_fixed_region(row);
    int32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region);
    uint32_t *synaptic_words = synapse_row_fixed_weight_controls(
        fixed_region);
    uint32_t new_synapse = _fixed_synapse_convert(id, weight, delay, type);

    // Add control word at offset
    synaptic_words[fixed_synapse] = new_synapse;

   // Increment FF
    fixed_region[0] = fixed_region[0] + 1;
    return true;
}

void synapses_flush_ring_buffer(uint32_t timestep) {

    uint32_t ring_buffer_index;

    for (uint32_t neuron_index = 0; neuron_index < n_neurons;
            neuron_index++) {

        // Loop through all synapse types
        for (uint32_t synapse_type_index = 0;
                synapse_type_index < n_synapse_types; synapse_type_index++) {

            // Get index in the ring buffers for the previous time slot for
            // this synapse type and neuron
            ring_buffer_index = synapses_get_ring_buffer_index(
                timestep, synapse_type_index, neuron_index, synapse_index_bits,
                synapse_index_bits);

            // Clear ring buffer
            ring_buffers[ring_buffer_index] = 0;
        }
    }

}

void synapses_set_contribution_region() {

    synaptic_region = sark_tag_ptr(memory_index, 0);
    synaptic_region += (offset << synapse_index_bits);
}
