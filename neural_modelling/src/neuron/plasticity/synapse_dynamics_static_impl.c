#include "synapse_dynamics.h"
#include <debug.h>

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

bool find_plastic_neuron_with_id(uint32_t id, address_t row,
                                 structural_plasticity_data_t *sp_data){
    use(id);
    use(row);
    use(sp_data);
    return false;
}

bool remove_plastic_neuron_at_offset(uint32_t offset, address_t row){
    use(offset);
    use(row);
    return false;
}

bool add_plastic_neuron_with_id(uint32_t id, address_t row, uint32_t weight,
                                uint32_t delay, uint32_t type){
    use(id);
    use(row);
    use(weight);
    use(delay);
    return false;
}
