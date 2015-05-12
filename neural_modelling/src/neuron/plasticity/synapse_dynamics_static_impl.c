#include "synapse_dynamics.h"
#include "../../common/constants.h"
#include <debug.h>

//! \brief initiliser for the plastic side of the model
//! \param[in] address the address in SDRAM where the plastic data is stored
//! \param[in] n_neurons the number of enurons this modle is expected to
//!                     simulate
//! \param[in] ring_buffer_to_input_buffer_left_shifts
//!      how much binary left shift to move stuff in the ring buffer by
//! \param[in] synapse_dynamics_magic_number the magic number for the dynamics
//! for this model
//! \param[in] synapse_plastic_strucutre the magic number for the way the
//! plastic rows are stored.
//! \param[in] time_dependency_magic_number the magic number for the timing
//! depednecny which this model was compiled with
//! \param[in] weight_dependency_magic_number the magic number for the
//! weight dependency which this model was compiled with
//! \return bool true if the initialiser succeds, false otherwise
bool synapse_dynamics_initialise(
        address_t address, uint32_t n_neurons,
        uint32_t *ring_buffer_to_input_buffer_left_shifts,
        uint32_t synapse_dynamics_magic_number,
        uint32_t synapse_plastic_strucutre_magic_number,
        uint32_t time_dependency_magic_number,
        uint32_t weight_dependency_magic_number) {
    use(address);
    use(n_neurons);
    use(ring_buffer_to_input_buffer_left_shifts);

    bool meets_dynamics_magic_number =
        synapse_dynamics_magic_number == SYNAPSE_DYNAMICS_STATIC;
    bool meets_plastic_structure =
        synapse_plastic_strucutre_magic_number == 0;
    bool meets_time_dependency_magic_number =
        time_dependency_magic_number == 0;
    bool meets_weight_dependency_magic_number =
        weight_dependency_magic_number == 0;
    if (meets_dynamics_magic_number && meets_time_dependency_magic_number &&
            meets_weight_dependency_magic_number && meets_plastic_structure){
        return true;
    }
    else{
        log_error("expected magic number 0x%x, 0x%x, 0x%x, 0x%x got magic "
                  "number 0x%x, 0x%x, 0x%x, 0x%x instead.",
                  SYNAPSE_DYNAMICS_STATIC, 0, 0, 0,
                  synapse_dynamics_magic_number,
                  synapse_plastic_strucutre_magic_number,
                  time_dependency_magic_number, weight_dependency_magic_number);
        return false;
    }
    return false;
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
