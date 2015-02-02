#include "../common/neuron-typedefs.h"
#include "../common/in_spikes.h"

#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <string.h>

#define APPLICATION_MAGIC_NUMBER 0xAC5

// Counters
#define N_COUNTERS       6
#define	MOTION_FORWARD   0x01
#define MOTION_BACK	     0x02
#define	MOTION_RIGHT     0x03
#define	MOTION_LEFT	     0x04
#define	MOTION_CLOCKWISE 0x05
#define	MOTION_C_CLKWISE 0x06
#define NEURON_ID_MASK   0x7FF

// Globals
static uint32_t time;
static uint32_t *counters;
static uint32_t *last_speed;
static uint32_t key;
static uint32_t speed;
static uint32_t sample_time;
static uint32_t update_time;
static uint32_t delay_time;
static int delta_threshold;
static uint32_t continue_if_not_different;
static uint32_t simulation_ticks;

static inline void send(uint32_t direction, uint32_t speed) {
    uint32_t direction_key = direction | key;
    while (!spin1_send_mc_packet(direction_key, speed, WITH_PAYLOAD)) {
        spin1_delay_us(1);
    }
    if (delay_time > 0) {
        spin1_delay_us(delay_time);
    }
}

static inline void do_motion(
        uint32_t direction_index, uint32_t opposite_index,
        const char *direction, const char *opposite) {
    int direction_count = (int) counters[direction_index - 1];
    int opposite_count = (int) counters[opposite_index - 1];
    int delta = direction_count - opposite_count;
    log_debug("%s = %d, %s = %d, delta = %d, threshold = %u", direction,
              direction_count, opposite, opposite_count, delta,
              delta_threshold);
    if (delta >= delta_threshold) {
        log_debug("Moving %s", direction);
        last_speed[direction_index - 1] = speed;
        last_speed[opposite_index - 1] = 0;
        send(direction_index, speed);
    } else if (delta <= -delta_threshold) {
        log_debug("Moving %s", direction);
        last_speed[direction_index - 1] = 0;
        last_speed[opposite_index - 1] = speed;
        send(opposite_index, speed);
    } else if (continue_if_not_different == 0) {
        log_debug("Motion is indeterminate in %s-%s direction", direction,
                  opposite);
        last_speed[direction_index - 1] = 0;
        last_speed[opposite_index - 1] = 0;
        send(direction_index, 0);
    }
}

static inline void do_update(
        uint32_t direction_index, uint32_t opposite_index,
        const char *direction, const char *opposite) {
    int direction_speed = (int) last_speed[direction_index - 1];
    int opposite_speed = (int) last_speed[opposite_index - 1];
    int delta = direction_speed - opposite_speed;
    if (delta > 0) {
        log_debug("Resending %s = %d", direction, direction_speed);
        send(direction_index, direction_speed);
    } else if (delta < 0) {
        log_debug("Resending %s = %d", opposite, opposite_speed);
        send(opposite_index, opposite_speed);
    } else {
        log_debug("Resending No Motion in the %s-%s direction", direction,
                  opposite);
        send(direction_index, 0);
    }
}

// Callbacks
void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    time++;

    log_debug("Timer tick %d", time);

    if ((simulation_ticks != UINT32_MAX) && (time == simulation_ticks)) {
        log_info("Simulation complete.\n");
        spin1_exit(0);
        return;
    }

    // Process the incoming spikes
    spike_t s;
    uint32_t nid;
    while (in_spikes_get_next_spike(&s)) {
        nid = (s & NEURON_ID_MASK);

        if (nid < N_COUNTERS) {
            counters[nid] += 1;
        } else {
            log_debug("Received spike from unknown neuron %d", nid);
        }
    }

    // Work out if there is any motion
    if ((time % sample_time) == 0) {

        // Do motion in pairs
        do_motion(MOTION_FORWARD, MOTION_BACK, "Forwards", "Backwards");
        do_motion(MOTION_LEFT, MOTION_RIGHT, "Left", "Right");
        do_motion(MOTION_CLOCKWISE, MOTION_C_CLKWISE, "Clockwise",
                  "Anti-clockwise");

        // Reset the counters
        for (uint32_t i = 0; i < N_COUNTERS; i++) {
            counters[i] = 0;
        }
    } else if ((time % update_time) == 0) {

        // Do updates in pairs
        do_update(MOTION_FORWARD, MOTION_BACK, "Forwards", "Backwards");
        do_update(MOTION_LEFT, MOTION_RIGHT, "Left", "Right");
        do_update(MOTION_CLOCKWISE, MOTION_C_CLKWISE, "Clockwise",
                  "Anti-clockwise");
    }
}

void read_parameters(address_t region_address) {
    log_info("Reading parameters from 0x%.8x", region_address);
    key = region_address[0];
    speed = region_address[1];
    sample_time = region_address[2];
    update_time = region_address[3];
    delay_time = region_address[4];
    delta_threshold = region_address[5];
    continue_if_not_different = region_address[6];

    // Allocate the space for the schedule
    counters = (uint32_t*) spin1_malloc(N_COUNTERS * sizeof(uint32_t));
    last_speed = (uint32_t*) spin1_malloc(N_COUNTERS * sizeof(uint32_t));

    for (uint32_t i = 0; i < N_COUNTERS; i++) {
        counters[i] = 0;
        last_speed[i] = 0;
    }

    log_info("Key = %d, speed = %d, sample_time = %d, update_time = %d,"
             " delay_time = %d, delta_threshold = %d,"
             " continue_if_not_different = %d",
             key, speed, sample_time, update_time, delay_time, delta_threshold,
             continue_if_not_different);
}

void incoming_spike_callback(uint key, uint payload) {
    use(payload);

    log_debug("Received spike %x at time %d\n", key, time);

    // If there was space to add spike to incoming spike queue
    in_spikes_add_spike(key);
}

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
    if (!simulation_read_timing_details(
            data_specification_get_region(0, address),
            APPLICATION_MAGIC_NUMBER, timer_period, &simulation_ticks)) {
        return false;
    }

    // Get the parameters
    read_parameters(data_specification_get_region(1, address));

    log_info("initialize: completed successfully");

    return true;
}

// Entry point
void c_main(void) {

    // Initialise
    uint32_t timer_period = 0;
    if (!initialize(&timer_period)) {
        log_error("Error in initialisation - exiting!");
        return;
    }

    // Initialize the incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(8192)) {
        return;
    }

    // Set timer_callback
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(MC_PACKET_RECEIVED, incoming_spike_callback, -1);
    spin1_callback_on(TIMER_TICK, timer_callback, 2);

    log_info("Starting");

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;
    simulation_run();
}
