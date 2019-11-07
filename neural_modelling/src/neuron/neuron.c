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

/*! \file
 *
 * \brief implementation of the neuron.h interface.
 *
 */

#include "neuron_base.h"
#include "implementations/neuron_impl.h"

//! \executes all the updates to neural parameters when a given timer period
//! has occurred.
//! \param[in] time the timer tick  value currently being executed
void neuron_do_timestep_update( // EXPORTED
        timer_t time, uint timer_count, uint timer_period) {
    // Set the next expected time to wait for between spike sending
    expected_time = sv->cpu_clk * timer_period;

    // Wait until recordings have completed, to ensure the recording space
    // can be re-written
    neuron_recording_wait_to_complete();
    neuron_recording_setup_for_next_recording();

    // Set up an array for storing the matrix recorded variable values
    uint32_t n_matrix_vars = neuron_recording_get_n_recorded_vars() - 1;
    state_t recorded_variable_values[n_matrix_vars];

    // update each neuron individually
    for (index_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {

        // Get external bias from any source of intrinsic plasticity
        input_t external_bias =
                synapse_dynamics_get_intrinsic_bias(time, neuron_index);

        // call the implementation function (boolean for spike)
        bool spike = neuron_impl_do_timestep_update(
                neuron_index, external_bias, recorded_variable_values);

        // Write the recorded variable values
        for (uint32_t i = 0; i < n_matrix_vars; i++) {
            neuron_recording_set_int32_recorded_param(
                i, neuron_index,
                recorded_variable_values[i]);
        }

        // If the neuron has spiked
        if (spike) {
            log_debug("neuron %u spiked at time %u", neuron_index, time);

            // Record the spike
            neuron_recording_set_spike(n_matrix_vars, neuron_index);

            // Do any required synapse processing
            synapse_dynamics_process_post_synaptic_event(time, neuron_index);

            if (use_key) {

                // Wait until the expected time to send
                while ((ticks == timer_count) &&
                        (tc[T1_COUNT] > expected_time)) {
                    // Do Nothing
                }
                expected_time -= time_between_spikes;

                // Send the spike
                while (!spin1_send_mc_packet(
                        key | neuron_index, 0, NO_PAYLOAD)) {
                    spin1_delay_us(1);
                }
            }
        } else {
            log_debug("the neuron %d has been determined to not spike",
                      neuron_index);
         }
    }

    // Disable interrupts to avoid possible concurrent access
    uint cpsr = 0;
    cpsr = spin1_int_disable();

    // Record the recorded variables
    neuron_recording_record(time);

    // Re-enable interrupts
    spin1_mode_restore(cpsr);
}
