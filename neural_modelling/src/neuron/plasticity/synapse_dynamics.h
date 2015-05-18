#ifndef _SYNAPSE_DYNAMICS_H_
#define _SYNAPSE_DYNAMICS_H_

#include "../../common/neuron-typedefs.h"
#include "../synapse_row.h"

//! \brief the initialiser for the plastic side of the neural edges
//! \param[in] address the address in SDRAM where plastic data is stored
//! \param[in] n_neurons the number of neurons this model is expected to
//!            simulate
//! \param[in] ring_buffer_to_input_buffer_left_shifts
//!            how much binary left shift to move stuff in the ring buffer by
//! \param[in] synapse_dynamics_magic_number the magic number which represetns
//!            which type of plastisity this model is implimenting
//! \param[in] synapse_plastic_strucutre_magic_number the magic number whihc
//!            represetns the way the synapse row data is stored
//! \param[in] time_dependency_magic_number the magic number which indicates
//!            which time dependence component this model is expected to use
//! \param[in] weight_dependency_magic_number the magic number which indicates
//!            which weight dependence component this model is expected to use
//! \return bool which is either true if all things were set up correctly or
//!              false otherwise
bool synapse_dynamics_initialise(
    address_t address, uint32_t n_neurons,
    uint32_t *ring_buffer_to_input_buffer_left_shifts,
    uint32_t synapse_dynamics_magic_number,
    uint32_t synapse_plastic_strucutre_magic_number,
    uint32_t time_dependency_magic_number,
    uint32_t weight_dependency_magic_number);

void synapse_dynamics_process_plastic_synapses(
    address_t plastic_region_address, address_t fixed_region_address,
    weight_t *ring_buffers, uint32_t time);

void synapse_dynamics_process_post_synaptic_event(
    uint32_t time, index_t neuron_index);

input_t synapse_dynamics_get_intrinsic_bias(uint32_t time, index_t neuron_index);

void synapse_dynamics_print_plastic_synapses(
        address_t plastic_region_address, address_t fixed_region_address,
        uint32_t *ring_buffer_to_input_buffer_left_shifts);

//! \either prints the counters for plastic pre synaptic events based
//! on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or does
//! nothing (the assumption being that a empty function will be removed by the
//! compiler and therefore there is no code bloat)
//! \return Nothing, this method does not return anything
void synapse_dynamics_print_plastic_pre_synaptic_events();

#endif // _SYNAPSE_DYNAMICS_H_
