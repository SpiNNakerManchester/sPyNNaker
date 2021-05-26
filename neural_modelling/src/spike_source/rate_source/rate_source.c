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

#define DMA_READ_TAG 0

// Declare spin1_wfi
extern void spin1_wfi(void);

// Spin1 API ticks - to know when the timer wraps
extern uint ticks;

//! spike source array region IDs in human readable form
typedef enum region {
    SYSTEM, RATE_PARAMS,
    PROVENANCE_REGION,
    PROFILER_REGION
} region;

#define NUMBER_OF_REGIONS_TO_RECORD 1
#define BYTE_TO_WORD_CONVERTER 4

typedef enum callback_priorities {
    MULTICAST = -1,
    SDP = 0,
    DMA = 1,
    TIMER = 2
} callback_priorities;

//! Parameters of the SpikeSourcePoisson
typedef struct global_parameters {
    //! True if there is a key to transmit, False otherwise
    bool has_key;
    //! The base key to send with (neuron ID to be added to it), or 0 if no key
    uint32_t key;
    //! The number of rates
    uint32_t elements;
    //! The offset of the timer ticks to desynchronize sources
    uint32_t timer_offset;

} global_parameters;

//! The global_parameters for the sub-population
static global_parameters params;

typedef struct rate_value {
    uint32_t time;
    uint32_t rate;
}rate_value;

struct config {

    global_parameters globals;
    uint32_t loop;
    rate_value rates[];
};

struct source_provenance {

    uint32_t current_timer_tick;
};

//! global variable which contains all the data for neurons
static rate_value *rates = NULL;
static rate_value *mem_region;

//! the time interval parameter TODO this variable could be removed and use the
//! timer tick callback timer value.
static uint32_t time;

//! the number of timer ticks that this model should run for before exiting.
static uint32_t simulation_ticks = 0;

//! the int that represents the bool for if the run is infinite or not.
static uint32_t infinite_run;

//! The timer period
static uint32_t timer_period;

static uint32_t index;
static uint32_t mem_index;
static size_t size;
static size_t region_size;

static uint32_t looping;
static uint32_t n_rates;

static uint32_t iteration;
static uint32_t expected;

static uint32_t last_rate_sent;


//! \brief method for reading the parameters stored in Poisson parameter region
//! \param[in] address the absolute SDRAM memory address to which the
//!            rate parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
static bool read_rate_parameters(struct config *config) {
    // Allocate DTCM for array of rates and copy block of data

    spin1_memcpy(&params, &config->globals, sizeof(params));

    if (params.elements > 0) {
        // the first time around, the array is set to NULL, afterwards,
        // assuming all goes well, there's an address here.
        size = params.elements > 1000 ? 1000 : params.elements;
        region_size = size * sizeof(rate_value);
        if (rates == NULL) {
            rates = spin1_malloc(region_size);
            // if failed to alloc memory, report and fail.
            if (rates == NULL) {
                log_error("Failed to allocate rates");
                return false;
            }
        }

        mem_region = config->rates;

        // store spike source data into DTCM
        spin1_memcpy(rates, mem_region, region_size);

        mem_index = size;

        looping = config->loop;
        n_rates = params.elements;
    }

    iteration = 0;
    expected = 0;

    log_info("read_rate_parameters: completed successfully");
    return true;
}

void store_provenance_data(address_t provenance_region) {

    log_debug("writing other provenance data");
    struct source_provenance *prov = (void *) provenance_region;

    // store the data into the provenance data region
    prov->current_timer_tick = time;
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
            data_specification_get_region(RATE_PARAMS, ds_regions))) {
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
            data_specification_get_region(RATE_PARAMS, ds_regions))) {
        log_error("failed to reread the Rate parameters from SDRAM");
        rt_error(RTE_SWERR);
    }

    log_info("Successfully resumed rate source at time: %u", time);

}

static void refresh(void) {

    spin1_dma_transfer(DMA_READ_TAG, mem_region + mem_index,
            rates, DMA_READ, region_size);

    mem_index += size;
    index = 0;
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

    //io_printf(IO_BUF, "%d %d %d\n", rates[index].time, rates[index].rate, time);

    uint32_t time_to_check;

    //LP TMP for US replica
    if(looping == 2 &&  time >= 20000) {

        return;

    }

    if(looping < 4) {

        if(index >= n_rates) {

            if(!iteration) {

                //FOR TESTING THE DELAYED EXC START, KEEP ONLY WHAT'S INSIDE THE IF CONDITION
                if(looping == 1)
                    expected = time;
                else
                    expected = index;
            }

            index = 0;
            iteration += expected;
        }

        time_to_check = rates[index].time + iteration;
    }
    else {

        time_to_check = rates[index].time;
    }

    if(time_to_check == time) {

        //URBANCZIK-SENN RESULTS, THIS IS TO HAVE A NON 0 INPUT AT EVERY TIMESTEP. REMOVE THE IF FOR NORMAL SIMS!
        if((time_to_check == 0) && (rates[index].rate == 0)) {

            while (!spin1_send_mc_packet(params.key, 0, WITH_PAYLOAD)) {
            spin1_delay_us(1);
            }

            //io_printf(IO_BUF, "%k t %d\n", 0, time);
        }
        else {

            while (!spin1_send_mc_packet(params.key, rates[index].rate, WITH_PAYLOAD)) {
                spin1_delay_us(1);
            }

            //io_printf(IO_BUF, "%k t %d\n", rates[index].rate, time);

            last_rate_sent = rates[index].rate;
        }

        index++;

        if(looping >= 4 && index >= 1000) {
            refresh();
        }
    }
    else if (looping < 4){

        while (!spin1_send_mc_packet(params.key, last_rate_sent, WITH_PAYLOAD)) {
            spin1_delay_us(1);
        }


       //io_printf(IO_BUF, "%k t %d\n", last_rate_sent, time);
    }
    else{

       while (!spin1_send_mc_packet(params.key, 0, WITH_PAYLOAD)) {
            spin1_delay_us(1);
        }
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

    index = 0;

    // Set timer tick (in microseconds)
    spin1_set_timer_tick_and_phase(timer_period, params.timer_offset);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    simulation_run();
}