#include "synapse_dynamics.h"
#include <debug.h>

// Pointers to neuron data
static neuron_pointer_t neuron_array_plasticity;
static additional_input_pointer_t additional_input_array_plasticity;
static threshold_type_pointer_t threshold_type_array_plasticity;

address_t synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(address);
    use(n_neurons);
    use(ring_buffer_to_input_buffer_left_shifts);
    return address;
}

//---------------------------------------
void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
}

//---------------------------------------
bool synapse_dynamics_process_plastic_synapses(address_t plastic_region_address,
        address_t fixed_region_address, weight_t *ring_buffer, uint32_t time) {
    use(plastic_region_address);
    use(fixed_region_address);
    use(ring_buffer);
    use(time);

    log_error("There should be no plastic synapses!");
    return false;
}

//---------------------------------------
input_t synapse_dynamics_get_intrinsic_bias(uint32_t time,
                                            index_t neuron_index) {
    use(time);
    use(neuron_index);
    return REAL_CONST(0.0);
}

void synapse_dynamics_print_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        uint32_t *ring_buffer_to_input_left_shifts) {
    use(plastic_region_address);
    use(fixed_region_address);
    use(ring_buffer_to_input_left_shifts);
}

uint32_t synapse_dynamics_get_plastic_pre_synaptic_events() {
    return 0;
}

uint32_t synapse_dynamics_get_plastic_saturation_count(){
	return 0;
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

//! \brief  Don't search the synaptic row for the the connection with the
//!         specified post-synaptic ID -- no rewiring here
//! \param[in] id: the (core-local) ID of the neuron to search for in the
//! synaptic row
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] sp_data: the address of a struct through which to return
//! weight, delay information
//! \return bool: was the search successful?
bool find_plastic_neuron_with_id(uint32_t id, address_t row,
                                 structural_plasticity_data_t *sp_data){
    use(id);
    use(row);
    use(sp_data);
    return false;
}

//! \brief  Don't remove the entry at the specified offset in the synaptic row
//! -- no rewiring here
//! \param[in] offset: the offset in the row at which to remove the entry
//! \param[in] row: the core-local address of the synaptic row
//! \return bool: was the removal successful?
bool remove_plastic_neuron_at_offset(uint32_t offset, address_t row){
    use(offset);
    use(row);
    return false;
}

//! \brief  Don't add a plastic entry in the synaptic row -- no rewiring here
//! \param[in] id: the (core-local) ID of the post-synaptic neuron to be added
//! \param[in] row: the core-local address of the synaptic row
//! \param[in] weight: the initial weight associated with the connection
//! \param[in] delay: the delay associated with the connection
//! \param[in] type: the type of the connection (e.g. inhibitory)
//! \return bool: was the addition successful?
bool add_plastic_neuron_with_id(uint32_t id, address_t row, uint32_t weight,
                                uint32_t delay, uint32_t type){
    use(id);
    use(row);
    use(weight);
    use(delay);
    use(type);
    return false;
}
