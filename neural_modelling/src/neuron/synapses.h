#ifndef _SYNAPSES_H_
#define _SYNAPSES_H_

#include <common/neuron-typedefs.h>
#include <neuron/structural_plasticity/sp_structs.h>
#include "synapse_row.h"

// Get the index of the ring buffer for a given timestep, synapse type and
// neuron index
static inline index_t synapses_get_ring_buffer_index(
        uint32_t simuation_timestep, uint32_t synapse_type_index,
        uint32_t neuron_index, uint32_t synapse_type_index_bits,
        uint32_t synapse_index_bits){
    return (((simuation_timestep & SYNAPSE_DELAY_MASK)
             << synapse_type_index_bits)
            | (synapse_type_index << synapse_index_bits)
            | neuron_index);
}

// Get the index of the ring buffer for a given timestep and combined
// synapse type and neuron index (as stored in a synapse row)
static inline index_t synapses_get_ring_buffer_index_combined(
        uint32_t simulation_timestep,
        uint32_t combined_synapse_neuron_index,
        uint32_t synapse_type_index_bits) {
    return (((simulation_timestep & SYNAPSE_DELAY_MASK)
             << synapse_type_index_bits)
            | combined_synapse_neuron_index);
}

// Converts a weight stored in a synapse row to an input
static inline input_t synapses_convert_weight_to_input(
        weight_t weight, uint32_t left_shift) {
    union {
        int_k_t input_type;
        s1615 output_type;
    } converter;

    converter.input_type = (int_k_t) (weight) << left_shift;

    return converter.output_type;
}

static inline void synapses_print_weight(
        weight_t weight, uint32_t left_shift) {
    if (weight != 0) {
        io_printf(IO_BUF, "%12.6k", synapses_convert_weight_to_input(
            weight, left_shift));
    } else {
        io_printf(IO_BUF, "      ");
    }
}

bool synapses_initialise(
    address_t synapse_params_address, address_t synaptic_matrix_address,
    uint32_t n_neurons, synapse_param_t **neuron_synapse_shaping_params_value,
    uint32_t **ring_buffer_to_input_buffer_left_shifts,
    address_t *indirect_synapses_address, address_t *direct_synapses_address);

void synapses_do_timestep_update(timer_t time);

//! \brief process a synaptic row
//! \param[in] time: the simulated time
//! \param[in] row: the synaptic row in question
//! \param[in] write: bool saying if to write this back to SDRAM
//! \param[in] process_id: ??????????????????
//! \return bool if successful or not
bool synapses_process_synaptic_row(
    uint32_t time, synaptic_row_t row, bool write, uint32_t process_id);

//! \brief returns the number of times the synapses have saturated their
//!        weights.
//! \return the number of times the synapses have saturated.
uint32_t synapses_get_saturation_count();

//! \brief returns the counters for plastic and fixed pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return the counter for plastic and fixed pre synaptic events or 0
uint32_t synapses_get_pre_synaptic_events();


//------------------------------------------------------------------------------
// Synaptic rewiring functions
//------------------------------------------------------------------------------

//! \brief  Searches the synaptic row for the the connection with the
//!         specified post-synaptic id
//! \param[in] id: the (core-local) id of the neuron to search for in the
//! synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[out] sp_data: the address of a struct through which to return
//! weight, delay information
//! \return bool: was the search successful?
bool find_static_neuron_with_id(uint32_t id, address_t row,
                                structural_plasticity_data_t *sp_data);

//! \brief  Remove the entry at the specified offset in the synaptic row
//! \param[in] offset: the offset in the row at which to remove the entry
//! \param[in] row: the core-local address of the synaptic row
//! \return bool: was the removal successful?
bool remove_static_neuron_at_offset(uint32_t offset, address_t row);

//! \brief  Add a static entry in the synaptic row
//! \param[in] is: the (core-local) id of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return bool: was the addition successful?
bool add_static_neuron_with_id(uint32_t id, address_t row, uint32_t weight,
                               uint32_t delay, uint32_t type);

#endif // _SYNAPSES_H_
