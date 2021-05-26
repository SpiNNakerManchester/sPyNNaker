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
 * \brief This file contains the main functions for a Poisson spike generator.
 */

#include <common/maths-util.h>

#include <data_specification.h>
#include <recording.h>
#include <debug.h>
#include <simulation.h>
#include <spin1_api.h>

#include <profiler.h>

// Declare spin1_wfi
extern void spin1_wfi(void);

// Spin1 API ticks - to know when the timer wraps
extern uint ticks;

//! spike source array region IDs in human readable form
typedef enum region {
    SYSTEM, RATE_PARAMS,
    RATE_VALUES,
    PROVENANCE_REGION,
    PROFILER_REGION
} region;

#define NUMBER_OF_REGIONS_TO_RECORD 1
#define BYTE_TO_WORD_CONVERTER 4
#define DMA_READ_TAG 0

typedef enum callback_priorities {
    MULTICAST = -1,
    SDP = 2,
    DMA = 1,
    TIMER = 1
} callback_priorities;

//! Parameters of the SpikeSourcePoisson
typedef struct global_parameters {
    //! True if there is a key to transmit, False otherwise
    bool has_key;
    //! The base key to send with (neuron ID to be added to it), or 0 if no key
    uint32_t key;
    //! The number of rates
    uint32_t generators;
    //! The offset of the timer ticks to desynchronize sources
    uint32_t timer_offset;
    //! The refresh rate for the input sequence in timesteps
    uint32_t refresh;
    //! The number of teaching signals written in memory
    uint32_t teaching_signals;

} global_parameters;

struct source_provenance {

    uint32_t current_timer_tick;
    uint32_t refresh_counts;
};

//! the time interval parameter TODO this variable could be removed and use the
//! timer tick callback timer value.
static uint32_t time;

//! the number of timer ticks that this model should run for before exiting.
static uint32_t simulation_ticks = 0;

//! the int that represents the bool for if the run is infinite or not.
static uint32_t infinite_run;

//! The timer period
static uint32_t timer_period;

static uint32_t key = 0;

//! Refresh frequency for the inputs
static uint32_t refresh;

static uint32_t refresh_counter;
static uint32_t total_n_refresh;
static uint32_t refresh_timer;

static uint32_t generators;

static uint8_t *rate_values;
static uint8_t *memory_values;

static uint32_t n_teaching_signals;
static uint32_t bytes_read;
static uint32_t max_size;

static uint32_t teaching_signal;

static uint32_t neg_teach = UINT32_MAX - ((1 << 20) - 1);

uint32_t elements;

uint32_t rate_value;

//! The size of the pool of rates to be sent
static uint32_t pool_size;

static inline void read_rate_values() {

    refresh_timer = 0;

    rate_value = rate_values[refresh_counter++];

    if(refresh_counter >= elements) {

        uint32_t size_to_read = 
            bytes_read + pool_size > max_size ? 
                max_size - bytes_read : pool_size;

        spin1_dma_transfer(
            DMA_READ_TAG, memory_values,
            rate_values, DMA_READ, size_to_read);

        memory_values += elements;
        refresh_counter = 0;
        bytes_read += size_to_read;
    }

    total_n_refresh++;
}


//! \brief method for reading the parameters stored in Poisson parameter region
//! \param[in] address the absolute SDRAM memory address to which the
//!            rate parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
static bool read_rate_parameters(address_t address, address_t starting_values) {
    // Allocate DTCM for array of rates and copy block of data

    global_parameters *params = (void *) address;

    generators = params->generators;

    // This ensures that we don't send a wrong teaching value on the first timestep
    rate_value = generators;

    refresh_timer = 0;
    refresh = params->refresh;
    if(params->has_key) {
        key = params->key;
    }

    n_teaching_signals = params->teaching_signals;

    elements = n_teaching_signals > 1024 ? 1024 : n_teaching_signals;
    max_size = n_teaching_signals > 1024 ? n_teaching_signals : 1024;

    max_size *= sizeof(uint8_t);

    pool_size = elements * sizeof(uint8_t);

    rate_values = spin1_malloc(pool_size);
    if (rate_values == NULL) {
        log_error("Could not allocate space for the rate values");
        return false;
    }

    spin1_memcpy(rate_values, starting_values, pool_size);

    bytes_read = pool_size;

    memory_values = (uint8_t *) starting_values;
    memory_values += elements;

    rate_value = rate_values[0];

    refresh_counter = 1;
    total_n_refresh = 1;

    // Storing 1 as S1615 to imporve performances when sending the teaching signal
    teaching_signal = 1 << 20;

    log_info("read_rate_parameters: completed successfully");
    return true;
}

void store_provenance_data(address_t provenance_region) {

    log_debug("writing other provenance data");
    struct source_provenance *prov = (void *) provenance_region;

    // store the data into the provenance data region
    prov->current_timer_tick = time;
    prov->refresh_counts = total_n_refresh;
    log_debug("finished other provenance data");
}

//! Initialises the model by reading in the regions and checking recording
//! data.
//! \param[out] timer_period a pointer for the memory address where the timer
//!            period should be stored during the function.
//! \param[out] update_sdp_port The SDP port on which to listen for rate
//!             updates
//! \return boolean of True if it successfully read all the regions and set up
//!         all its internal data structures. Otherwise returns False
static bool initialize(void) {
    log_info("Initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(ds_regions)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM, ds_regions),
            APPLICATION_NAME_HASH, &timer_period, &simulation_ticks,
            &infinite_run, &time, SDP, DMA)) {
        return false;
    }
    simulation_set_provenance_function(
            store_provenance_data,
            data_specification_get_region(PROVENANCE_REGION, ds_regions));

    if (!read_rate_parameters(
            data_specification_get_region(RATE_PARAMS, ds_regions),
            data_specification_get_region(RATE_VALUES, ds_regions))) {
        return false;
    }

    // Setup profiler
    profiler_init(
            data_specification_get_region(PROFILER_REGION, ds_regions));

    log_info("Initialise: completed successfully");

    return true;
}

//! \brief runs any functions needed at resume time.
//! \return None
static void resume_callback(void) {
    recording_reset();

    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    if (!read_rate_parameters(
            data_specification_get_region(RATE_PARAMS, ds_regions),
            data_specification_get_region(RATE_VALUES, ds_regions))) {
        log_error("failed to reread the Rate parameters from SDRAM");
        rt_error(RTE_SWERR);
    }

    log_info("Successfully resumed rate source at time: %u", time);

}


//! \brief Timer interrupt callback
//! \param[in] timer_count the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused for consistency sake of the API always returning two
//!            parameters, this parameter has no semantics currently and thus
//!            is set to 0
//! \return None
static void timer_callback(uint timer_count, uint unused) {
    use(unused);
    use(timer_count);

    profiler_write_entry_disable_irq_fiq(PROFILER_ENTER | PROFILER_TIMER);

    time++;
    refresh_timer++;

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (infinite_run != TRUE && time >= simulation_ticks) {
        // go into pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);

        profiler_finalise();

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time--;
        simulation_ready_to_read();
        return;
    }

    for(index_t i = 0; i < generators; i++) {

        if(rate_value == i) {
            
            while (!spin1_send_mc_packet(key | i, teaching_signal, WITH_PAYLOAD)) {
                    spin1_delay_us(2);
                }
        }
        else {
            while (!spin1_send_mc_packet(key | i, neg_teach, WITH_PAYLOAD)) {
                    spin1_delay_us(2);
                }
        }
        spin1_delay_us(2);
    }

    if(refresh_timer > refresh) {
        read_rate_values();
    }

    profiler_write_entry_disable_irq_fiq(PROFILER_EXIT | PROFILER_TIMER);
}


//! The entry point for this model
void c_main(void) {
    // Load DTCM data
    if (!initialize()) {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    io_printf(IO_BUF, " neg teach %k\n", neg_teach);

    // Set timer tick (in microseconds)
    spin1_set_timer_tick_and_phase(timer_period, 0);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    simulation_run();
}