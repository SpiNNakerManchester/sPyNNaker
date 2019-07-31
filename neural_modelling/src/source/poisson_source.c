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
 *  \brief This file contains the main functions for a poisson source
 *         (the idea behind it being that it doesn't generate spikes,
 *         but rather writes a "weight array" to SDRAM which is then
 *         used as noise on a neuron that knows about this array).
 *
 */

#include <common/maths-util.h>

#include <data_specification.h>
#include <debug.h>
#include <random.h>
#include <simulation.h>
#include <spin1_api.h>
#include <stdfix-full-iso.h>
#include <limits.h>
#include <utils.h>
#include "spin1_api_params.h"


// Declare spin1_wfi
extern void spin1_wfi();

// Spin1 API ticks - to know when the timer wraps
extern uint ticks;

//! data structure for poisson sources
typedef struct poisson_source_t {
    uint32_t start_ticks;
    uint32_t end_ticks;
    bool is_fast_source;

    UFRACT exp_minus_lambda;
    REAL sqrt_lambda;
    uint32_t mean_isi_ticks;
    uint32_t time_to_source_ticks;

	REAL poisson_weight;
} poisson_source_t;

//! spike source array region IDs in human readable form
typedef enum region {
    SYSTEM, POISSON_PARAMS,
    PROVENANCE_REGION,
} region;

//#define NUMBER_OF_REGIONS_TO_RECORD 1
#define BYTE_TO_WORD_CONVERTER 4
//! A scale factor to allow the use of integers for "inter-spike intervals"
#define ISI_SCALE_FACTOR 1000

// some of these callbacks are probably not necessary... ?
typedef enum callback_priorities{
    MULTICAST = -1, SDP = 0, TIMER = 2, DMA = 1
} callback_priorities;

//! Parameters of the PoissonSource
struct global_parameters {
    //! The offset of the timer ticks to desynchronize sources
    uint32_t timer_offset;

    //! The expected time to wait between spikes
    uint32_t time_between_sources;

    //! The time between ticks in seconds for setting the rate
    UFRACT seconds_per_tick;

    //! The number of ticks per second for setting the rate
    uint32_t ticks_per_second;

    //! The border rate between slow and fast sources
    REAL slow_rate_per_tick_cutoff;

    //! The border rate between fast and faster sources
    REAL fast_rate_per_tick_cutoff;

    //! The ID of the first source relative to the population as a whole
    uint32_t first_source_id;

    //! The number of sources in this sub-population
    uint32_t n_sources;

    //! The seed for the Poisson generation process
    mars_kiss64_seed_t source_seed;
};

//! The global_parameters for the sub-population
static struct global_parameters global_parameters;

//! global variable which contains all the data for neurons
static poisson_source_t *poisson_parameters = NULL;

//! The expected current clock tick of timer_1
static uint32_t expected_time;

//! the time interval parameter TODO this variable could be removed and use the
//! timer tick callback timer value.
static uint32_t time;

//! the number of timer ticks that this model should run for before exiting.
static uint32_t simulation_ticks = 0;

//! the int that represents the bool for if the run is infinite or not.
static uint32_t infinite_run;

//! The size of each source buffer in bytes
static uint32_t source_buffer_size; // is this needed?

//! The source buffer itself
static REAL* source_buffer;

//! The timer period
static uint32_t timer_period;

static uint16_t *poisson_region;
static uint32_t contribution_offset;
static uint32_t memory_index;
static uint32_t dma_size;

//! \brief deduces the time in timer ticks multiplied by ISI_SCALE_FACTOR
//!        until the next source is to occur given the mean inter-source interval
//! \param[in] mean_inter_source_interval_in_ticks The mean number of ticks
//!            before a source is expected to occur in a slow process.
//! \return a uint32_t which represents "time" in timer ticks * ISI_SCALE_FACTOR
//!         until the next source is used
static inline uint32_t slow_source_get_time_to_source(
	    uint32_t mean_inter_source_interval_in_ticks) {
	// Round (dist variate * ISI_SCALE_FACTOR), convert to uint32
	int nbits = 15;
	uint32_t value = (uint32_t) roundk(exponential_dist_variate(
			mars_kiss64_seed, global_parameters.source_seed) * ISI_SCALE_FACTOR, nbits);
	// Now multiply by the mean ISI
	uint32_t exp_variate = value * mean_inter_source_interval_in_ticks;
	// Note that this will be compared to ISI_SCALE_FACTOR in the main loop!
    return exp_variate;
}

//! \brief Determines the value to multiply the weight by on this timestep, for a fast source
//! \param[in] exp_minus_lambda exp(-lambda), lambda is amount of spikes expected to be
//!            produced this timer interval (timer tick in real time)
//! \return a uint32_t which represents the number of spikes to transmit
//!         this timer tick
static inline uint32_t fast_source_get_num_weight_multiples(
        UFRACT exp_minus_lambda) {
	// If the value of exp_minus_lambda is very small then it's not worth
	// using the algorithm, so just return 0
    if (bitsulr(exp_minus_lambda) == bitsulr(UFRACT_CONST(0.0))) {
        return 0;
    }
    else {
        return poisson_dist_variate_exp_minus_lambda(
            mars_kiss64_seed,
            global_parameters.source_seed, exp_minus_lambda);
    }
}

//! \brief Determines the value to multiply the weight by on this timestep, for a faster source
//!        (where lambda is large enough that a Gaussian can be used instead of a Poisson)
//! \param[in] sqrt_lambda Square root of the amount of spikes expected to be produced
//!            this timer interval (timer tick in real time)
//! \return a uint32_t which represents the number of spikes to transmit
//!         this timer tick
static inline uint32_t faster_source_get_num_weight_multiples(
        REAL sqrt_lambda) {
    // First we do x = (invgausscdf(U(0,1)) * 0.5) + sqrt(lambda)
    REAL x = (gaussian_dist_variate(
			mars_kiss64_seed,
			global_parameters.source_seed) * REAL_CONST(0.5)) + sqrt_lambda;
    // Then we return int(roundk(x^2))
    int nbits = 15;
    return (uint32_t) roundk(x * x, nbits);
}

void print_sources(){
    for (index_t s = 0; s < global_parameters.n_sources; s++) {
        log_info("atom %d", s);
        log_info("scaled_start = %u", poisson_parameters[s].start_ticks);
        log_info("scaled end = %u", poisson_parameters[s].end_ticks);
        log_info("is_fast_source = %d", poisson_parameters[s].is_fast_source);
        log_info(
            "exp_minus_lambda = %k",
            (REAL)(poisson_parameters[s].exp_minus_lambda));
        log_info("sqrt_lambda = %k", poisson_parameters[s].sqrt_lambda);
        log_info("isi_val = %u", poisson_parameters[s].mean_isi_ticks);
        log_info(
            "time_to_source = %u", poisson_parameters[s].time_to_source_ticks);
        log_info(
            "poisson_weight = %k", poisson_parameters[s].poisson_weight);
    }
}

void start_dma_transfer(void *system_address, void *tcm_address,
    uint direction, uint length) {

    uint cpsr;

    cpsr = spin1_int_disable();

    uint desc = DMA_WIDTH << 24 | DMA_BURST_SIZE << 21 | direction << 19 | length;

    // Be careful, this transfer is done with no checks for maximum performances!
    // OK ONLY FOR STATIC NETWORK IN WHICH WE ARE SURE THAT WE HAVE NO MORE THAN 2 TRANSFERS AT A TIME
    dma[DMA_ADRS] = (uint) system_address;
    dma[DMA_ADRT] = (uint) tcm_address;
    dma[DMA_DESC] = desc;

    spin1_mode_restore(cpsr);
}

//! \brief entry method for reading the global parameters stored in Poisson
//!        parameter region
//! \param[in] address the absolute SDRAM memory address to which the
//!            Poisson parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
bool read_global_parameters(address_t address) {

    log_info("read global_parameters: starting");

    spin1_memcpy(&global_parameters, address, sizeof(global_parameters));

    log_info(
        "\t timer_offset = %u", global_parameters.timer_offset);

    log_info("\t seed = %u %u %u %u",
    	global_parameters.source_seed[0],
        global_parameters.source_seed[1],
        global_parameters.source_seed[2],
        global_parameters.source_seed[3]);

    validate_mars_kiss64_seed(global_parameters.source_seed);

    log_info(
        "\t spike sources = %u, starting at %u",
        global_parameters.n_sources, global_parameters.first_source_id);
    log_info(
        "seconds_per_tick = %k\n",
        (REAL)(global_parameters.seconds_per_tick));
    log_info("ticks_per_second = %u\n", global_parameters.ticks_per_second);
    log_info(
        "slow_rate_per_tick_cutoff = %k\n",
        global_parameters.slow_rate_per_tick_cutoff);
    log_info(
        "fast_rate_per_tick_cutoff = %k\n",
        global_parameters.fast_rate_per_tick_cutoff);

    memory_index = *(address + (sizeof(global_parameters) / 4));

    uint32_t n_atoms_power_2 = global_parameters.n_sources;
    uint32_t log_n_atoms = 1;
    if (global_parameters.n_sources != 1) {
        if (!is_power_of_2(global_parameters.n_sources)) {
            n_atoms_power_2 = next_power_of_2(global_parameters.n_sources);
        }
        log_n_atoms = ilog_2(n_atoms_power_2);
    }

    contribution_offset = log_n_atoms;
    dma_size = global_parameters.n_sources * sizeof(uint16_t);

    log_info("read_global_parameters: completed successfully");
    return true;
}

//! \brief method for reading the parameters stored in Poisson parameter region
//! \param[in] address the absolute SDRAm memory address to which the
//!            Poisson parameter region starts.
//! \return a boolean which is True if the parameters were read successfully or
//!         False otherwise
static bool read_poisson_parameters(address_t address) {

    // Allocate DTCM for array of spike sources and copy block of data
    if (global_parameters.n_sources > 0) {

        // the first time around, the array is set to NULL, afterwards,
        // assuming all goes well, there's an address here.
        if (poisson_parameters == NULL){
            poisson_parameters = (poisson_source_t*) spin1_malloc(
                global_parameters.n_sources * sizeof(poisson_source_t));
        }

        // if failed to alloc memory, report and fail.
        if (poisson_parameters == NULL) {
            log_error("Failed to allocate poisson_parameters");
            return false;
        }

        // store spike source data into DTCM
        uint32_t spikes_offset = (sizeof(global_parameters) / 4) + 1;
        spin1_memcpy(
            poisson_parameters, &address[spikes_offset],
            global_parameters.n_sources * sizeof(poisson_source_t));
    }
    log_info("read_poisson_parameters: completed successfully");
    return true;
}

//! Initialises the model by reading in the regions and checking recording
//! data.
//! \param[out] timer_period a pointer for the memory address where the timer
//!            period should be stored during the function.
//! \param[out] update_sdp_port The SDP port on which to listen for rate
//!             updates
//! \return boolean of True if it successfully read all the regions and set up
//!         all its internal data structures. Otherwise returns False
static bool initialize() {
    log_info("Initialize: started");

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
    simulation_set_provenance_data_address(
            data_specification_get_region(PROVENANCE_REGION, ds_regions));

    // Setup regions that specify spike source array data
    if (!read_global_parameters(
            data_specification_get_region(POISSON_PARAMS, ds_regions))) {
        return false;
    }

    if (!read_poisson_parameters(
            data_specification_get_region(POISSON_PARAMS, ds_regions))) {
        return false;
    }

    // Set up buffer for storage of stuff
    source_buffer_size = global_parameters.n_sources * sizeof(REAL);
    source_buffer = (REAL *) spin1_malloc(source_buffer_size);

    // Loop through spike sources and initialise
    // Loop through slow spike sources and initialise 1st time to spike
    for (index_t s = 0; s < global_parameters.n_sources; s++) {
        if (!poisson_parameters[s].is_fast_source) {
            poisson_parameters[s].time_to_source_ticks =
                slow_source_get_time_to_source(
                    poisson_parameters[s].mean_isi_ticks);
        }
    	source_buffer[s] = REAL_CONST(0.0);
    }

    // print spike sources for debug purposes
    //print_sources();

    log_info("Initialize: completed successfully");

    return true;
}

//! \brief runs any functions needed at resume time.
//! \return None
void resume_callback() {
//    recording_reset();

    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    if (!read_poisson_parameters(
            data_specification_get_region(POISSON_PARAMS, ds_regions))){
        log_error("failed to reread the Poisson parameters from SDRAM");
        rt_error(RTE_SWERR);
    }

    // Loop through slow spike sources and initialise 1st time to spike
    for (index_t s = 0; s < global_parameters.n_sources; s++) {
        if (!poisson_parameters[s].is_fast_source &&
                poisson_parameters[s].time_to_source_ticks == 0) {
            poisson_parameters[s].time_to_source_ticks =
                slow_source_get_time_to_source(
                    poisson_parameters[s].mean_isi_ticks);
        }
    	source_buffer[s] = REAL_CONST(0.0);
    }

    log_info("Successfully resumed Poisson spike source at time: %u", time);

    // print spike sources for debug purposes
//    print_sources();
}

//! \brief stores the Poisson parameters back into SDRAM for reading by the
//! host when needed
//! \return None
bool store_poisson_parameters() {
    log_info("stored_parameters: starting");

    // Get the address this core's DTCM data starts at from SRAM
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();
    address_t param_store =
            data_specification_get_region(POISSON_PARAMS, ds_regions);

    // Copy the global_parameters back to SDRAM
    spin1_memcpy(param_store, &global_parameters, sizeof(global_parameters));

    // store spike source parameters into array into SDRAM for reading by
    // the host
    if (global_parameters.n_sources > 0) {
        uint32_t spikes_offset =
                sizeof(global_parameters) / BYTE_TO_WORD_CONVERTER;
        spin1_memcpy(
                &param_store[spikes_offset], poisson_parameters,
                global_parameters.n_sources * sizeof(poisson_source_t));
    }

    log_info("stored_parameters : completed successfully");
    return true;
}

//! \brief adds weights to array as required
//! \param[in] neuron_id: the neurons to store values from
//! \param[in] n_spikes: the number of times to multiply weight by
//!
static inline void _add_weight(uint32_t neuron_id, uint32_t n) {
	source_buffer[neuron_id] += n * poisson_parameters[neuron_id].poisson_weight;
}

static inline void _set_contribution_region() {

    poisson_region = sark_tag_ptr(memory_index, 0);
    poisson_region += (3 << contribution_offset);
}

//! \brief Timer interrupt callback
//! \param[in] timer_count the number of times this call back has been
//!            executed since start of simulation
//! \param[in] unused for consistency sake of the API always returning two
//!            parameters, this parameter has no semantics currently and thus
//!            is set to 0
//! \return None
void timer_callback(uint timer_count, uint unused) {
	use(timer_count);
    use(unused);

    // Disable DMA_DONE interrupts for the simulation
    vic[VIC_DISABLE] = (1 << DMA_DONE_INT);

    time++;

    if(time == 0) {

        _set_contribution_region();
    }

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (infinite_run != TRUE && time >= simulation_ticks) {

        // Enable DMA_DONE interrupt when the simulation ends
        vic[VIC_ENABLE] = (1 << DMA_DONE_INT);

        // go into pause and resume state to avoid another tick
        simulation_handle_pause_resume(resume_callback);

        // rewrite poisson params to SDRAM for reading out if needed
        if (!store_poisson_parameters()){
            log_error("Failed to write poisson parameters to SDRAM");
            rt_error(RTE_SWERR);
        }

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time -= 1;
        simulation_ready_to_read();
        return;
    }

    // Set the next expected time to wait for between spike sending
    expected_time = sv->cpu_clk * timer_period;

    // Loop through spike sources
    for (index_t s = 0; s < global_parameters.n_sources; s++) {

        // If this spike source is active this tick
        poisson_source_t *source = &poisson_parameters[s];

        // Choose between fast or slow spike sources
        if (source->is_fast_source) {
            if (time >= source->start_ticks
                    && time < source->end_ticks) {

                // Get number of multiples to send this tick
            	uint32_t num_weight_multiples = 0;
            	// If sqrt_lambda has been set then use the Gaussian algorithm for faster sources
            	if (REAL_COMPARE(source->sqrt_lambda, >, REAL_CONST(0.0))) {
            	    num_weight_multiples = faster_source_get_num_weight_multiples(
            				source->sqrt_lambda);
            	} else {
            		// Call the fast source Poisson algorithm
            		num_weight_multiples = fast_source_get_num_weight_multiples(
            				source->exp_minus_lambda);
            	}

                // If there are any
                if (num_weight_multiples > 0) {

                    // Write spikes to out spikes
                    _add_weight(s, num_weight_multiples);

                }
            }
        } else {
            // Handle slow sources
            if ((time >= source->start_ticks)
                    && (time < source->end_ticks)
                    && (source->mean_isi_ticks != 0)) {

                // Mark a spike while the "timer" is below the scale factor value
                while (source->time_to_source_ticks < ISI_SCALE_FACTOR) {

                    // Write weight value to this source
                	_add_weight(s, 1);

                    // Update time to spike (note, this might not get us back above
                    // the scale factor, particularly if the mean_isi is smaller)
                    source->time_to_source_ticks +=
                        slow_source_get_time_to_source(
                            source->mean_isi_ticks);
                }

                // Now we have finished for this tick, subtract the scale factor
                source->time_to_source_ticks -= ISI_SCALE_FACTOR;
            }
        }
    }

    start_dma_transfer(poisson_region, source_buffer, DMA_WRITE, dma_size);

    while(!(dma[DMA_STAT] & 0x400));
    dma[DMA_CTRL] = 0x08;

    // at this point we have looped over all the sources, so we can write the array
    // to wherever it needs to go; for now I'm just printing it
    for (index_t s = 0; s < global_parameters.n_sources; s++) {
    	source_buffer[s] = REAL_CONST(0.0);
    }

}

////! \brief set the spike source rate as required
////! \param[in] id, the ID of the source to be updated
////! \param[in] rate, the REAL-valued rate in Hz, to be multiplied
////!            to get per_tick values
//void set_source_rate(uint32_t id, REAL rate) {
//    if ((id >= global_parameters.first_source_id) &&
//            ((id - global_parameters.first_source_id) <
//             global_parameters.n_sources)) {
//        uint32_t sub_id = id - global_parameters.first_source_id;
//        log_debug("Setting rate of %u (%u) to %kHz", id, sub_id, rate);
//        REAL rate_per_tick = rate * global_parameters.seconds_per_tick;
//        if (rate >= global_parameters.slow_rate_per_tick_cutoff) {
//            poisson_parameters[sub_id].is_fast_source = true;
//            if (rate >= global_parameters.fast_rate_per_tick_cutoff) {
//            	poisson_parameters[sub_id].sqrt_lambda =
//            			SQRT(rate_per_tick); // warning: sqrtk is untested...
//            } else {
//            	poisson_parameters[sub_id].exp_minus_lambda =
//            			(UFRACT) EXP(-rate_per_tick);
//            }
//        } else {
//            poisson_parameters[sub_id].is_fast_source = false;
//            poisson_parameters[sub_id].mean_isi_ticks =
//                (uint32_t) rate * global_parameters.ticks_per_second;
//        }
//    }
//}

//// Is this function actually used any more?
//void sdp_packet_callback(uint mailbox, uint port) {
//    use(port);
//    sdp_msg_t *msg = (sdp_msg_t *) mailbox;
//    uint32_t *data = (uint32_t *) &(msg->cmd_rc);
//
//    uint32_t n_items = data[0];
//    data = &(data[1]);
//    for (uint32_t item = 0; item < n_items; item++) {
//        uint32_t id = data[(item * 2)];
//        REAL rate = kbits(data[(item * 2) + 1]);
//        set_source_rate(id, rate);
//    }
//    spin1_msg_free(msg);
//}

////! multicast callback used to set rate when injected in a live example
//void multicast_packet_callback(uint key, uint payload) {
//    uint32_t id = key & global_parameters.set_rate_neuron_id_mask;
//    REAL rate = kbits(payload);
//    set_source_rate(id, rate);
//}

//! The entry point for this model
void c_main(void) {

    // Load DTCM data
    if (!initialize()) {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Set timer tick (in microseconds)
    spin1_set_timer_tick_and_phase(
        timer_period, global_parameters.timer_offset);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);
//    spin1_callback_on(
//        MCPL_PACKET_RECEIVED, multicast_packet_callback, MULTICAST);

    simulation_run();
}
