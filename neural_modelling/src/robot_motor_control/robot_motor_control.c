/*
 * Copyright (c) 2017-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \dir
//! \brief Robot motor controller pseudo-neuron implementation
//! \file
//! \brief Implementation of Robot Motor Control model

#include <common/neuron-typedefs.h>
#include <common/in_spikes.h>

#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <stdbool.h>

// ----------------------------------------------------------------------

//! The structure of our configuration region in SDRAM
typedef struct {
    //! The (base) key to use to send to the motor
    uint32_t key;
    //! The standard motor speed scaling factor
    int speed;
    //! Time interval between samples of the state of incoming messages,
    //! in ticks
    uint32_t sample_time;
    //! Time interval between motor speed updates, in ticks
    uint32_t update_time;
    //! Outgoing inter-message delay time, in &mu;s
    uint32_t delay_time;
    //! The size of change required to matter
    int delta_threshold;
    //! Whether we should continue moving if there is no change
    uint32_t continue_if_not_different;
} motor_control_config_t;

//! The provenance information written on application shutdown.
struct robot_motor_control_provenance {
    //! A count of the times that the synaptic input circular buffers overflowed
    uint32_t n_input_buffer_overflows;
};

//! Number of counters
#define N_COUNTERS         6

//! The "directions" that the motors can move in
typedef enum {
    MOTION_FORWARD = 0x01,    //!< Forwards
    MOTION_BACK	= 0x02,       //!< Backwards
    MOTION_RIGHT = 0x03,      //!< To the right
    MOTION_LEFT	= 0x04,       //!< To the left
    MOTION_CLOCKWISE = 0x05,  //!< Rotate clockwise on the spot
    MOTION_C_CLOCKWISE = 0x06 //!< Rotate counterclockwise on the spot
} direction_t;

//! Mask for selecting the neuron ID from a spike
#define NEURON_ID_MASK     0x7FF

// Globals
//! The simulation time
static uint32_t time;
//! Accumulators for each motor direction
static int *counters;
//! The last speeds for each motor direction
static int *last_speed;
//! The (base) key to use to send to the motor
static uint32_t key;
//! The standard motor speed, set by configuration
static int speed;
//! Time interval between samples, in ticks
static uint32_t sample_time;
//! Time interval between updates, in ticks
static uint32_t update_time;
//! Inter-message delay time, in &mu;s
static uint32_t delay_time;
//! The size of change required to matter
static int delta_threshold;
//! Whether we should continue moving if there is no change
static bool continue_if_not_different;
//! Current simulation stop/pause time
static uint32_t simulation_ticks;
//! True if the simulation is running continuously
static uint32_t infinite_run;

//! DSG regions in use
enum robot_motor_control_regions_e {
    SYSTEM_REGION, //!< General simulation API control area
    PARAMS_REGION,  //!< Configuration region for this application
    PROVENANCE_DATA_REGION //!< Provenance region for this application
};

//! values for the priority for each callback
enum robot_motor_control_callback_priorities {
    MC = -1,   //!< Multicast message reception is FIQ
    SDP = 0,   //!< SDP handling is highest normal priority
    DMA = 1,   //!< DMA complete handling is medium priority
    TIMER = 2, //!< Timer interrupt processing is lowest priority
};

// ----------------------------------------------------------------------

//! \brief Send a SpiNNaker multicast-with-payload message to the motor hardware
//! \param[in] direction: Which direction to move in
//! \param[in] the_speed: What speed to move at
static inline void send_to_motor(uint32_t direction, uint32_t the_speed) {
    uint32_t direction_key = direction | key;
    while (!spin1_send_mc_packet(direction_key, the_speed, WITH_PAYLOAD)) {
        spin1_delay_us(1);
    }
    if (delay_time > 0) {
        spin1_delay_us(delay_time);
    }
}

//! \brief Commands the robot's motors to start doing a motion
//! \param[in] direction_index: The "forward" sense of motion
//! \param[in] opposite_index: The "reverse" sense of motion
//! \param[in] direction: for debugging
//! \param[in] opposite: for debugging
static inline void do_motion(
        direction_t direction_index, direction_t opposite_index,
        const char *direction, const char *opposite) {
    int direction_count = counters[direction_index - 1];
    int opposite_count = counters[opposite_index - 1];
    int delta = direction_count - opposite_count;
    log_debug("%s = %d, %s = %d, delta = %d, threshold = %u",
            direction, direction_count, opposite, opposite_count, delta,
            delta_threshold);

    if (delta >= delta_threshold) {
        log_debug("Moving %s", direction);
        last_speed[direction_index - 1] = speed;
        last_speed[opposite_index - 1] = 0;
        send_to_motor(direction_index, speed);
    } else if (delta <= -delta_threshold) {
        log_debug("Moving %s", direction);
        last_speed[direction_index - 1] = 0;
        last_speed[opposite_index - 1] = speed;
        send_to_motor(opposite_index, speed);
    } else if (!continue_if_not_different) {
        log_debug("Motion is indeterminate in %s-%s direction",
                direction, opposite);
        last_speed[direction_index - 1] = 0;
        last_speed[opposite_index - 1] = 0;
        send_to_motor(direction_index, 0);
    }
}

//! \brief Commands the robot's motors to continue a motion started by
//!     do_motion()
//! \param[in] direction_index: The "forward" sense of motion
//! \param[in] opposite_index: The "reverse" sense of motion
//! \param[in] direction: for debugging
//! \param[in] opposite: for debugging
static inline void do_update(
        direction_t direction_index, direction_t opposite_index,
        const char *direction, const char *opposite) {
    int direction_speed = last_speed[direction_index - 1];
    int opposite_speed = last_speed[opposite_index - 1];
    int delta = direction_speed - opposite_speed;
    if (delta > 0) {
        log_debug("Resending %s = %d", direction, direction_speed);
        send_to_motor(direction_index, direction_speed);
    } else if (delta < 0) {
        log_debug("Resending %s = %d", opposite, opposite_speed);
        send_to_motor(opposite_index, opposite_speed);
    } else {
        log_debug("Resending No Motion in the %s-%s direction", direction,
                opposite);
        send_to_motor(direction_index, 0);
    }
}

// Callbacks
//! \brief Regular 1ms callback. Takes spikes from circular buffer and converts
//!     to motor activity level.
//! \param unused0: unused
//! \param unused1: unused
static void timer_callback(UNUSED uint unused0, UNUSED uint unused1) {
    time++;

    log_debug("Timer tick %d", time);

    if (simulation_is_finished()) {
        simulation_handle_pause_resume(NULL);
        log_info("Simulation complete.\n");
        simulation_ready_to_read();
    }

    // Process the incoming spikes
    spike_t s;
    uint32_t nid;
    while (in_spikes_get_next_spike(&s)) {
        nid = (s & NEURON_ID_MASK);

        if (nid < N_COUNTERS) {
            counters[nid]++;
        } else {
            log_debug("Received spike from unknown neuron %d", nid);
        }
    }

    // Work out if there is any motion
    if (time % sample_time == 0) {
        // Do motion in pairs
        do_motion(MOTION_FORWARD, MOTION_BACK, "Forwards", "Backwards");
        do_motion(MOTION_LEFT, MOTION_RIGHT, "Left", "Right");
        do_motion(MOTION_CLOCKWISE, MOTION_C_CLOCKWISE, "Clockwise",
                "Anti-clockwise");

        // Reset the counters
        for (uint32_t i = 0; i < N_COUNTERS; i++) {
            counters[i] = 0;
        }
    } else if ((time % update_time) == 0) {
        // Do updates in pairs
        do_update(MOTION_FORWARD, MOTION_BACK, "Forwards", "Backwards");
        do_update(MOTION_LEFT, MOTION_RIGHT, "Left", "Right");
        do_update(MOTION_CLOCKWISE, MOTION_C_CLOCKWISE, "Clockwise",
                "Anti-clockwise");
    }
}

//! \brief Reads the configuration
//! \param[in] config_region: Where to read the configuration from
static void read_parameters(motor_control_config_t *config_region) {
    log_info("Reading parameters from 0x%.8x", config_region);
    key = config_region->key;
    speed = config_region->speed;
    sample_time = config_region->sample_time;
    update_time = config_region->update_time;
    delay_time = config_region->delay_time;
    delta_threshold = config_region->delta_threshold;
    continue_if_not_different = config_region->continue_if_not_different;

    // Allocate the space for the schedule
    counters = spin1_malloc(N_COUNTERS * sizeof(int));
    last_speed = spin1_malloc(N_COUNTERS * sizeof(int));

    for (uint32_t i = 0; i < N_COUNTERS; i++) {
        counters[i] = 0;
        last_speed[i] = 0;
    }

    log_info("Key = %d, speed = %d, sample_time = %d, update_time = %d,"
            " delay_time = %d, delta_threshold = %d, continue_if_not_different = %d",
            key, speed, sample_time, update_time, delay_time, delta_threshold,
            continue_if_not_different);
}

//! \brief Add incoming spike message (in FIQ) to circular buffer
//! \param[in] key: The received spike
//! \param payload: ignored
static void incoming_spike_callback(uint key, UNUSED uint payload) {
    log_debug("Received spike %x at time %d\n", key, time);

    // If there was space to add spike to incoming spike queue
    in_spikes_add_spike(key);
}

//! \brief Add incoming spike message (in FIQ) to circular buffer
//! \param[in] key: The received spike
//! \param payload: ignored
static void incoming_spike_callback_payload(uint key, uint payload) {
    use(payload);

    log_debug("Received spike %x at time %d\n", key, time);

    // If there was space to add spike to incoming spike queue
    for (uint count = 0; count < payload; count ++){
        in_spikes_add_spike(key);
    }
}

//! \brief Callback to store provenance data (format: neuron_provenance).
//! \param[out] provenance_region: Where to write the provenance data
static void c_main_store_provenance_data(address_t provenance_region) {
    log_debug("writing other provenance data");
    struct robot_motor_control_provenance *prov = (void *) provenance_region;

    // store the data into the provenance data region
    prov->n_input_buffer_overflows = in_spikes_get_n_buffer_overflows();

    log_debug("finished other provenance data");
}

//! \brief Read all application configuration
//! \param[out] timer_period: How long to program ticks to be
//! \return True if initialisation succeeded
static bool initialize(uint32_t *timer_period) {
    log_info("initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    data_specification_metadata_t *ds_regions =
            data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(ds_regions)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM_REGION, ds_regions),
            APPLICATION_NAME_HASH, timer_period, &simulation_ticks,
            &infinite_run, &time, SDP, DMA)) {
        return false;
    }

    simulation_set_provenance_function(
        c_main_store_provenance_data,
        data_specification_get_region(PROVENANCE_DATA_REGION, ds_regions));

    // Get the parameters
    read_parameters(data_specification_get_region(PARAMS_REGION, ds_regions));

    log_info("initialise: completed successfully");

    return true;
}

//! Entry point
void c_main(void) {
    // Initialise
    uint32_t timer_period = 0;
    if (!initialize(&timer_period)) {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    // Initialise the incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(8192)) {
        return;
    }

    // Set timer_callback
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(MC_PACKET_RECEIVED, incoming_spike_callback, MC);
    spin1_callback_on(
        MCPL_PACKET_RECEIVED, incoming_spike_callback_payload, MC);
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;
    simulation_run();
}
