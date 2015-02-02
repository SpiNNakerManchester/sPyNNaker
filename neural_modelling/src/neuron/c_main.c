/*
 * c_main.c
 *
 * SUMMARY
 *  This file contains the main function of the application framework, which
 *  the application programmer uses to configure and run applications.
 *
 * AUTHOR
 *    Thomas Sharp - thomas.sharp@cs.man.ac.uk
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *    A header file that can be used as the API for the spin-neuron.a library.
 *    To use the code is compiled with
 *
 *      #include "debug.h"
 *
 *  CREATION DATE
 *    21 July, 2013
 *
 *  HISTORY
 *    DETAILS
 *    Created on       : 27 July 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 */

#include "../common/in_spikes.h"
#include "neuron.h"
#include "synapses.h"
#include "spike_processing.h"
#include "population_table.h"
#include "plasticity/synapse_dynamics.h"

#include <data_specification.h>
#include <simulation.h>
#include <debug.h>

#ifndef APPLICATION_MAGIC_NUMBER
#define APPLICATION_MAGIC_NUMBER 0
#error APPLICATION_MAGIC_NUMBER was undefined.  Make sure you define this\
       constant
#endif

#define N_RECORDING_CHANNELS 3

typedef enum regions_e {
    SYSTEM_REGION,
    NEURON_PARAMS_REGION,
    SYNAPSE_PARAMS_REGION,
    POPULATION_TABLE_REGION,
    SYNAPTIC_MATRIX_REGION,
    SYNAPSE_DYNAMICS_REGION,
    SPIKE_RECORDING_REGION,
    POTENTIAL_RECORDING_REGION,
    GSYN_RECORDING_REGION
} regions_e;

uint32_t time;
static uint32_t simulation_ticks = 0;

// Globals
#ifdef SYNAPSE_BENCHMARK
  uint32_t  num_fixed_pre_synaptic_events = 0;
  uint32_t  num_plastic_pre_synaptic_events = 0;
#endif  // SYNAPSE_BENCHMARK

static bool initialize(uint32_t *timer_period) {
    log_info("initialize: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    uint32_t version;
    if (!data_specification_read_header(address, &version)) {
        return false;
    }

    // Get the timing details
    address_t system_region = data_specification_get_region(
        SYSTEM_REGION, address);
    if (!simulation_read_timing_details(
            system_region, APPLICATION_MAGIC_NUMBER, timer_period,
            &simulation_ticks)) {
        return false;
    }

    // Set up recording
    recording_channel_e channels_to_record[] = {
        e_recording_channel_spike_history,
        e_recording_channel_neuron_potential,
        e_recording_channel_neuron_gsyn
    };
    regions_e regions_to_record[] = {
        SPIKE_RECORDING_REGION,
        POTENTIAL_RECORDING_REGION,
        GSYN_RECORDING_REGION
    };
    uint32_t region_sizes[N_RECORDING_CHANNELS];
    uint32_t recording_flags;
    recording_read_region_sizes(
        &system_region[SIMULATION_N_TIMING_DETAIL_WORDS],
        &recording_flags, &region_sizes[0], &region_sizes[1], &region_sizes[2]);
    for (uint32_t i = 0; i < N_RECORDING_CHANNELS; i++) {
        if (recording_is_channel_enabled(recording_flags,
                                         channels_to_record[i])) {
            if (!recording_initialze_channel(
                    data_specification_get_region(regions_to_record[i],
                                                  address),
                    channels_to_record[i], region_sizes[i])) {
                return false;
            }
        }
    }

    // Set up the neurons
    uint32_t n_neurons;
    if (!neuron_initialise(
            data_specification_get_region(NEURON_PARAMS_REGION, address),
            recording_flags, &n_neurons)) {
        return false;
    }

    // Set up the synapses
    input_t *input_buffers;
    uint32_t *ring_buffer_to_input_buffer_left_shifts;
    if (!synapses_initialise(
            data_specification_get_region(SYNAPSE_PARAMS_REGION, address),
            n_neurons, &input_buffers,
            &ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }
    neuron_set_input_buffers(input_buffers);

    // Set up the population table
    uint32_t row_max_n_words;
    if (!population_table_initialise(
            data_specification_get_region(POPULATION_TABLE_REGION, address),
            data_specification_get_region(SYNAPTIC_MATRIX_REGION, address),
            &row_max_n_words)) {
        return false;
    }

    // Set up the synapse dynamics
    if (!synapse_dynamics_initialise(
            data_specification_get_region(SYNAPSE_DYNAMICS_REGION, address),
            n_neurons, ring_buffer_to_input_buffer_left_shifts)) {
        return false;
    }

    if (!spike_processing_initialise(row_max_n_words)) {
        return false;
    }

    return true;
}

void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);

    time++;

    log_info("Timer tick %u", time);

    // if a fixed number of simulation ticks are specified and these have passed
    if (simulation_ticks != UINT32_MAX && time >= simulation_ticks) {
        log_info("Simulation complete.\n");

#ifdef SYNAPSE_BENCHMARK
        log_info("\t%u/%u fixed/plastic pre-synaptic events.\n",
                 num_fixed_pre_synaptic_events,
                 num_plastic_pre_synaptic_events);
#endif  // SYNAPSE_BENCHMARK

        synapses_print_saturation_count();

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        recording_finalise();

        // Check for buffer overflow
        uint spike_buffer_overflows = in_spikes_get_n_buffer_overflows();
        if (spike_buffer_overflows > 0) {
            io_printf(IO_STD, "\tWarning - %d spike buffers overflowed\n",
                    spike_buffer_overflows);
        }

        spin1_exit(0);
        return;
    }

    synapses_do_timestep_update(time);
    neuron_do_timestep_update(time);
}

void c_main(void) {

    // Load DTCM data
    uint32_t timer_period;
    initialize(&timer_period);

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Set up the timer tick callback (others are handled elsewhere)
    spin1_callback_on(TIMER_TICK, timer_callback, 2);

    log_info("Starting");
    simulation_run();
}
