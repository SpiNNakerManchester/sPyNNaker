#include "synapse_dynamics.h"
#include <debug.h>

bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    use(address);
    use(n_neurons);
    use(ring_buffer_to_input_buffer_left_shifts);
    return true;
}

//---------------------------------------
void synapse_dynamics_process_post_synaptic_event(
        uint32_t time, index_t neuron_index) {
    use(time);
    use(neuron_index);
}

//---------------------------------------
void synapse_dynamics_process_plastic_synapses(address_t plastic_region_address,
        address_t fixed_region_address, weight_t *ring_buffer, uint32_t time) {
    use(plastic_region_address);
    use(fixed_region_address);
    use(ring_buffer);
    use(time);

    log_error("There should be no plastic synapses!");
}

//---------------------------------------
input_t synapse_dynamics_get_intrinsic_bias(index_t neuron_index) {
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

//! \As a fixed synapse dynamics has no plastic pre synaptic events, this
//! method does nothing, but is needed by the synapse dynamics.h file
//! (the assumption being that a empty function will be removed by the
//! compiler and therefore there is no code bloat)
//! \return Nothing, this method does not return anything
void synapse_dynamics_print_plastic_pre_synaptic_events(){
}
