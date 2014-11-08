#include "../common/in_spikes.h"
#include "../common/out_spikes.h"

#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <spin1_api.h>

#include <string.h>

// Constants
#define DELAY_STAGE_LENGTH  16
#define APPLICATION_MAGIC_NUMBER 0xAC4

// Globals
static uint32_t key = 0;
static uint32_t num_neurons = 0;
static uint32_t time = UINT32_MAX;
static uint32_t simulation_ticks = 0;

static uint8_t **spike_counters = NULL;
static bit_field_t *neuron_delay_stage_config = NULL;
static uint32_t num_delay_stages = 0;
static uint32_t num_delay_slots_mask = 0;
static uint32_t neuron_bit_field_words = 0;

static bool processing_spikes = false;

static inline uint32_t round_to_next_pot(uint32_t v) {
    v--;
    v |= v >> 1;
    v |= v >> 2;
    v |= v >> 4;
    v |= v >> 8;
    v |= v >> 16;
    v++;
    return v;
}

static bool read_parameters(address_t address) {

    log_info("read_parameters: starting");

    // changed from above for new file format 13-1-2014
    key = address[0];
    log_info("\tkey = %08x, (x: %u, y: %u) proc: %u", key, key_x(key),
            key_y(key), key_p(key));

    num_neurons = address[1];
    neuron_bit_field_words = get_bit_field_size(num_neurons);

    num_delay_stages = address[2];
    uint32_t num_delay_slots = num_delay_stages * DELAY_STAGE_LENGTH;
    uint32_t num_delay_slots_pot = round_to_next_pot(num_delay_slots);
    num_delay_slots_mask = (num_delay_slots_pot - 1);

    log_info("\tparrot neurons = %u, neuron bit field words = %u,"
            " num delay stages = %u, num delay slots = %u (pot = %u),"
            " num delay slots mask = %08x",
            num_neurons, neuron_bit_field_words,
            num_delay_stages, num_delay_slots, num_delay_slots_pot,
            num_delay_slots_mask);

    // Create array containing a bitfield specifying whether each neuron should
    // emit spikes after each delay stage
    neuron_delay_stage_config = (bit_field_t*) spin1_malloc(
            num_delay_stages * sizeof(bit_field_t));

    // Loop through delay stages
    for (uint32_t d = 0; d < num_delay_stages; d++) {
        log_info("\tdelay stage %u", d);

        // Allocate bit-field
        neuron_delay_stage_config[d] = (bit_field_t) spin1_malloc(
                neuron_bit_field_words * sizeof(uint32_t));

        // Copy delay stage configuration bits into delay stage configuration bit-field
        address_t neuron_delay_stage_config_data_address = &address[3]
                + (d * neuron_bit_field_words);
        memcpy(neuron_delay_stage_config[d],
                neuron_delay_stage_config_data_address,
                neuron_bit_field_words * sizeof(uint32_t));

        for (uint32_t w = 0; w < neuron_bit_field_words; w++) {
            log_debug("\t\tdelay stage config word %u = %08x", w,
                    neuron_delay_stage_config[d][w]);
        }
    }

    // Allocate array of counters for each delay slot
    spike_counters = (uint8_t**) spin1_malloc(
            num_delay_slots_pot * sizeof(uint8_t*));

    for (uint32_t s = 0; s < num_delay_slots_pot; s++) {

        // Allocate an array of counters for each neuron and zero
        spike_counters[s] = (uint8_t*) spin1_malloc(
                num_neurons * sizeof(uint8_t));
        memset(spike_counters[s], 0, num_neurons * sizeof(uint8_t));
    }

    log_info("read_parameters: completed successfully");
    return true;
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
    if (!read_parameters(data_specification_get_region(1, address))) {
        return false;
    }

    log_info("initialize: completed successfully");

    return true;
}

// Callbacks
void incoming_spike_callback(uint key, uint payload) {
    use(payload);

    log_debug("Received spike %x", key);

    // If there was space to add spike to incoming spike queue
    if (in_spikes_add_spike(key)) {
        if (!processing_spikes) {
            processing_spikes = true;
            spin1_trigger_user_event(0, 0);
        }
    }
}

void spike_process(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);

    // Get current time slot of incoming spike counters
    uint32_t current_time_slot = time & num_delay_slots_mask;
    uint8_t *current_time_slot_spike_counters =
            spike_counters[current_time_slot];

    log_debug("Current time slot %u", current_time_slot);

    // Zero all counters in current time slot
    memset(current_time_slot_spike_counters, 0, sizeof(uint8_t) * num_neurons);

    // While there are any incoming spikes
    spike_t s;
    while (in_spikes_next_spike(&s)) {

        // Mask out neuron id
        uint32_t neuron_id = (s & KEY_MASK);
        if (neuron_id < num_neurons) {
            // Increment counter
            current_time_slot_spike_counters[neuron_id]++;
            log_debug("Incrementing counter %u = %u\n", neuron_id,
                    current_time_slot_spike_counters[neuron_id]);
        } else {
            log_debug("Invalid neuron ID %u", neuron_id);
        }
    }

    processing_spikes = false;
}

void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);

    time++;

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (simulation_ticks != UINT32_MAX && time >= simulation_ticks) {
        log_info("Simulation complete.\n");
        spin1_exit(0);
    }

    // Loop through delay stages
    for (uint32_t d = 0; d < num_delay_stages; d++) {

        // If any neurons emit spikes after this delay stage
        bit_field_t delay_stage_config = neuron_delay_stage_config[d];
        if (nonempty_bit_field(delay_stage_config, neuron_bit_field_words)) {

            // Get key mask for this delay stage and it's time slot
            uint32_t delay_stage_key_mask = key | (d << 8);
            uint32_t delay_stage_delay = (d + 1) * DELAY_STAGE_LENGTH;
            uint32_t delay_stage_time_slot = (((int32_t) time
                    - (int32_t) delay_stage_delay)
                    & (int32_t) num_delay_slots_mask);
            uint8_t *delay_stage_spike_counters =
                    spike_counters[delay_stage_time_slot];

            log_debug("Checking time slot %u for delay stage %u",
                    delay_stage_time_slot, d);

            // Loop through neurons
            for (uint32_t n = 0; n < num_neurons; n++) {
                // If this neuron emits a spike after this stage
                if (bit_field_test(delay_stage_config, n)) {

                    // Calculate key all spikes coming from this neuron will be
                    // sent with
                    uint32_t spike_key = n | delay_stage_key_mask;

#ifdef LOG_LEVEL >= LOG_DEBUG
                    if(delay_stage_spike_counters[n] > 0)
                    {
                        log_debug("Neuron %u sending %u spikes after delay"
                                "stage %u with key %x",
                                n, delay_stage_spike_counters[n], d, spike_key);
                    }
#endif  // DEBUG

                    // Loop through counted spikes and send
                    for (uint32_t s = 0; s < delay_stage_spike_counters[n];
                            s++) {
                        spin1_send_mc_packet(spike_key, NULL, NO_PAYLOAD);
                    }
                }
            }
        }
    }

    // Zero all counters in current time slot
    uint32_t current_time_slot = time & num_delay_slots_mask;
    uint8_t *current_time_slot_spike_counters =
            spike_counters[current_time_slot];
    memset(current_time_slot_spike_counters, 0, sizeof(uint8_t) * num_neurons);
}

// Entry point
void c_main(void) {

    // Initialise
    uint32_t timer_period = 0;
    if (!initialize(&timer_period)) {
        log_error("Error in initialisation - exiting!");
        return;
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Initialize the incoming spike buffer
    initialize_spike_buffer(IN_SPIKE_SIZE);

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(MC_PACKET_RECEIVED, incoming_spike_callback, -1);
    spin1_callback_on(USER_EVENT, spike_process, 1);
    spin1_callback_on(TIMER_TICK, timer_callback, 2);

    log_info("Starting");
    simulation_run();
}
