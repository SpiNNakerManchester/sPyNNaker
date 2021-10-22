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
#endif

// Globals required for synapse benchmarking to work.
uint32_t  num_fixed_pre_synaptic_events = 0;

// The number of neurons
static uint32_t n_neurons;

// The number of synapse types
static uint32_t n_synapse_types;

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


/* PRIVATE FUNCTIONS */

#if LOG_LEVEL >= LOG_DEBUG
static const char *_get_type_char(uint32_t synapse_type) {
	return neuron_get_synapse_type_char(synapse_type);
}
#endif // LOG_LEVEL >= LOG_DEBUG

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
            _get_type_char(synapse_type),
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
            const char *type_string = _get_type_char(t);
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
                           synapse_type_index_bits, synapse_index_bits);
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
    neuron_print_inputs();
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

    num_fixed_pre_synaptic_events += fixed_synapse;

    for (; fixed_synapse > 0; fixed_synapse--) {

        // Get the next 32 bit word from the synaptic_row
        // (should auto increment pointer in single instruction)
        uint32_t synaptic_word = *synaptic_words++;

        // Extract components from this word
        uint32_t delay = synapse_row_sparse_delay(synaptic_word,
            synapse_type_index_bits);
        uint32_t combined_synapse_neuron_index = synapse_row_sparse_type_index(
                synaptic_word, synapse_type_index_mask);

        int32_t weight = synapse_row_sparse_weight(synaptic_word);
        io_printf(IO_BUF, "signed w: %d \n", weight);

        // Convert into ring buffer offset
        uint32_t ring_buffer_index = synapses_get_ring_buffer_index_combined(
            delay + time, combined_synapse_neuron_index,
            synapse_type_index_bits);

        // Add weight to current ring buffer value
        int32_t accumulation = ring_buffers[ring_buffer_index] + weight;

        // If 17th bit is set, saturate accumulator at UINT16_MAX (0xFFFF)
        // **NOTE** 0x10000 can be expressed as an ARM literal,
        //          but 0xFFFF cannot.  Therefore, we use (0x10000 - 1)
        //          to obtain this value
//        uint32_t sat_test = accumulation & 0x10000;
//        if (sat_test) {
//            accumulation = sat_test - 1;
//            saturation_count += 1;
//        }

        // Store saturated value back in ring-buffer
        ring_buffers[ring_buffer_index] = accumulation;
    }
}

//! private method for doing output debug data on the synapses
static inline void _print_synapse_parameters() {
//! only if the models are compiled in debug mode will this method contain
//! said lines.
#if LOG_LEVEL >= LOG_DEBUG
	// again neuron_synapse_shaping_params has moved to implementation
	neuron_print_synapse_parameters();
#endif // LOG_LEVEL >= LOG_DEBUG
}


/* INTERFACE FUNCTIONS */
bool synapses_initialise(
        address_t synapse_params_address, address_t direct_matrix_address,
        uint32_t n_neurons_value, uint32_t n_synapse_types_value,
        uint32_t **ring_buffer_to_input_buffer_left_shifts,
        address_t *direct_synapses_address) {

    log_debug("synapses_initialise: starting");
    n_neurons = n_neurons_value;
    n_synapse_types = n_synapse_types_value;

    // Set up ring buffer left shifts
    ring_buffer_to_input_left_shifts = (uint32_t *) spin1_malloc(
        n_synapse_types * sizeof(uint32_t));
    spin1_memcpy(
        ring_buffer_to_input_left_shifts, synapse_params_address,
        n_synapse_types * sizeof(uint32_t));
    *ring_buffer_to_input_buffer_left_shifts =
        ring_buffer_to_input_left_shifts;

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

    log_debug("synapses_initialise: completed successfully");
    _print_synapse_parameters();

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
    }
    for (uint32_t i = 0; i < ring_buffer_size; i++) {
        ring_buffers[i] = 0;
    }

    synapse_type_index_bits = log_n_neurons + log_n_synapse_types;
    synapse_type_index_mask = (1 << synapse_type_index_bits) - 1;
    synapse_index_bits = log_n_neurons;
    synapse_index_mask = (1 << synapse_index_bits) - 1;
    synapse_type_bits = log_n_synapse_types;
    synapse_type_mask = (1 << log_n_synapse_types) - 1;
    return true;
}

void synapses_do_timestep_update(timer_t time) {

    _print_ring_buffers(time);

    // Disable interrupts to stop DMAs interfering with the ring buffers
    uint32_t state = spin1_irq_disable();

    // Transfer the input from the ring buffers into the input buffers
    for (uint32_t neuron_index = 0; neuron_index < n_neurons;
            neuron_index++) {

        // Loop through all synapse types
        for (uint32_t synapse_type_index = 0;
                synapse_type_index < n_synapse_types; synapse_type_index++) {

            // Get index in the ring buffers for the current time slot for
            // this synapse type and neuron
            uint32_t ring_buffer_index = synapses_get_ring_buffer_index(
                time, synapse_type_index, neuron_index, synapse_type_index_bits,
                synapse_index_bits);

            // Convert ring-buffer entry to input and add on to correct
            // input for this synapse type and neuron
            // SD 02/02/21:
            //log_info("T: %u  ", time);
            neuron_add_inputs(
                synapse_type_index, neuron_index,
                synapses_convert_weight_to_input(
                    ring_buffers[ring_buffer_index],
                    ring_buffer_to_input_left_shifts[synapse_type_index]));

            // Clear ring buffer
            ring_buffers[ring_buffer_index] = 0;
        }
    }

    _print_inputs();

    // Re-enable the interrupts
    spin1_mode_restore(state);
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
