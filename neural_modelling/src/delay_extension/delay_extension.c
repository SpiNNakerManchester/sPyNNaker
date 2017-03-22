#include "../common/neuron-typedefs.h"
#include "../common/in_spikes.h"

#include <bit_field.h>
#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <spin1_api.h>

#include <string.h>

// Constants
#define DELAY_STAGE_LENGTH  16

//! values for the priority for each callback
typedef enum callback_priorities {
    MC_PACKET = -1, SDP = 0, USER = 1, TIMER = 2
} callback_priorities;

//! region identifiers
typedef enum region_identifiers{
    SYSTEM = 0, DELAY_PARAMS = 1, PROVENANCE_REGION = 2
} region_identifiers;

enum parameter_positions {
    KEY, INCOMING_KEY, INCOMING_MASK, N_ATOMS, N_DELAY_STAGES,
    RANDOM_BACKOFF, TIME_BETWEEN_SPIKES, DELAY_BLOCKS
};

typedef enum extra_provenance_data_region_entries{
    N_PACKETS_RECEIVED = 0,
    N_PACKETS_PROCESSED = 1,
    N_PACKETS_ADDED = 2,
    N_PACKETS_SENT = 3,
    N_BUFFER_OVERFLOWS = 4,
    N_DELAYS = 5
} extra_provenance_data_region_entries;

// Globals
static uint32_t key = 0;
static uint32_t incoming_key = 0;
static uint32_t incoming_mask = 0;
static uint32_t incoming_neuron_mask = 0;
static uint32_t num_neurons = 0;
static uint32_t time = UINT32_MAX;
static uint32_t simulation_ticks = 0;
static uint32_t infinite_run;

static uint8_t **spike_counters = NULL;
static bit_field_t *neuron_delay_stage_config = NULL;
static uint32_t num_delay_stages = 0;
static uint32_t num_delay_slots_mask = 0;
static uint32_t neuron_bit_field_words = 0;

static uint32_t n_in_spikes = 0;
static uint32_t n_processed_spikes = 0;
static uint32_t n_spikes_sent = 0;
static uint32_t n_spikes_added = 0;

//! An amount of microseconds to back off before starting the timer, in an
//! attempt to avoid overloading the network
static uint32_t random_backoff_us;

//! The number of clock ticks between processing each neuron at each delay
//! stage
static uint32_t time_between_spikes;

//! The expected current clock tick of timer_1 to wait for
static uint32_t expected_time;

static uint32_t n_delays = 0;


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

    key = address[KEY];
    incoming_key = address[INCOMING_KEY];
    incoming_mask = address[INCOMING_MASK];
    incoming_neuron_mask = ~incoming_mask;
    log_info(
        "\t key = 0x%08x, incoming key = 0x%08x, incoming mask = 0x%08x,"
        "incoming key mask = 0x%08x",
        key, incoming_key, incoming_mask, incoming_neuron_mask);

    num_neurons = address[N_ATOMS];
    neuron_bit_field_words = get_bit_field_size(num_neurons);

    num_delay_stages = address[N_DELAY_STAGES];
    random_backoff_us = address[RANDOM_BACKOFF];
    time_between_spikes = address[TIME_BETWEEN_SPIKES] * sv->cpu_clk;

    uint32_t num_delay_slots = num_delay_stages * DELAY_STAGE_LENGTH;
    uint32_t num_delay_slots_pot = round_to_next_pot(num_delay_slots);
    num_delay_slots_mask = (num_delay_slots_pot - 1);

    log_info("\t parrot neurons = %u, neuron bit field words = %u,"
             " num delay stages = %u, num delay slots = %u (pot = %u),"
             " num delay slots mask = %08x",
             num_neurons, neuron_bit_field_words,
             num_delay_stages, num_delay_slots, num_delay_slots_pot,
             num_delay_slots_mask);

    log_info(
        "\t random back off = %u, time_between_spikes = %u",
        random_backoff_us, time_between_spikes);

    // Create array containing a bitfield specifying whether each neuron should
    // emit spikes after each delay stage
    neuron_delay_stage_config = (bit_field_t*) spin1_malloc(
        num_delay_stages * sizeof(bit_field_t));

    // Loop through delay stages
    for (uint32_t d = 0; d < num_delay_stages; d++) {
        log_info("\t delay stage %u", d);

        // Allocate bit-field
        neuron_delay_stage_config[d] = (bit_field_t) spin1_malloc(
            neuron_bit_field_words * sizeof(uint32_t));

        // Copy delay stage configuration bits into delay stage configuration bit-field
        address_t neuron_delay_stage_config_data_address =
            &address[DELAY_BLOCKS] + (d * neuron_bit_field_words);
        memcpy(neuron_delay_stage_config[d],
               neuron_delay_stage_config_data_address,
               neuron_bit_field_words * sizeof(uint32_t));

        for (uint32_t w = 0; w < neuron_bit_field_words; w++) {
            log_debug("\t\t delay stage config word %u = %08x", w,
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

void _store_provenance_data(address_t provenance_region){
    log_debug("writing other provenance data");

    // store the data into the provenance data region
    provenance_region[N_PACKETS_RECEIVED] = n_in_spikes;
    provenance_region[N_PACKETS_PROCESSED] = n_processed_spikes;
    provenance_region[N_PACKETS_ADDED] = n_spikes_added;
    provenance_region[N_PACKETS_SENT] = n_spikes_sent;
    provenance_region[N_BUFFER_OVERFLOWS] = in_spikes_get_n_buffer_overflows();
    provenance_region[N_DELAYS] = n_delays;
    log_debug("finished other provenance data");
}

static bool initialize(uint32_t *timer_period) {
    log_info("initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(address)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(SYSTEM, address),
            APPLICATION_NAME_HASH, timer_period, &simulation_ticks,
            &infinite_run, SDP, _store_provenance_data,
            data_specification_get_region(PROVENANCE_REGION, address))) {
        return false;
    }

    // Get the parameters
    if (!read_parameters(data_specification_get_region(
            DELAY_PARAMS, address))) {
        return false;
    }

    log_info("initialise: completed successfully");

    return true;
}

// Callbacks
void incoming_spike_callback(uint key, uint payload) {
    use(payload);

    log_debug("Received spike %x", key);
    n_in_spikes += 1;

    // If there was space to add spike to incoming spike queue
    in_spikes_add_spike(key);
}

// Gets the neuron id of the incoming spike
static inline key_t _key_n(key_t k) {
    return k & incoming_neuron_mask;
}

static void spike_process() {

    // turn off inturppts as this function is criticle for
    // keeping time in sync.
    uint state = spin1_int_disable();

    // Get current time slot of incoming spike counters
    uint32_t current_time_slot = time & num_delay_slots_mask;
    uint8_t *current_time_slot_spike_counters =
        spike_counters[current_time_slot];

    log_debug("Current time slot %u", current_time_slot);

    // While there are any incoming spikes
    spike_t s;
    while (in_spikes_get_next_spike(&s)) {
        n_processed_spikes += 1;

        if ((s & incoming_mask) == incoming_key) {

            // Mask out neuron id
            uint32_t neuron_id = _key_n(s);
            if (neuron_id < num_neurons) {

                // Increment counter
                current_time_slot_spike_counters[neuron_id]++;
                log_debug("Incrementing counter %u = %u\n", neuron_id,
                          current_time_slot_spike_counters[neuron_id]);
                n_spikes_added += 1;
            } else {
                log_debug("Invalid neuron ID %u", neuron_id);
            }
        } else {
            log_debug("Invalid spike key 0x%08x", s);
        }
    }

    // reactivate interupts as criticle section complete
    spin1_mode_restore(state);
}

void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);

    // Process all the spikes from the last timestep
    spike_process();

    time++;

    log_debug("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (infinite_run != TRUE && time >= simulation_ticks) {

        // handle the pause and resume functionality
        simulation_handle_pause_resume(NULL);

        log_info(
            "Delay extension finished at time %u, %u received spikes, "
            "%u processed spikes, %u sent spikes, %u added spikes",
            time, n_in_spikes, n_processed_spikes, n_spikes_sent,
            n_spikes_added);

        log_info("Delayed %u times", n_delays);

        // Subtract 1 from the time so this tick gets done again on the next
        // run
        time -= 1;
        return;
    }

    // Sleep for a random time
    spin1_delay_us(random_backoff_us);

    // Set the next expected time to wait for between spike sending
    expected_time = tc[T1_COUNT] - time_between_spikes;

    // Loop through delay stages
    for (uint32_t d = 0; d < num_delay_stages; d++) {

        // If any neurons emit spikes after this delay stage
        bit_field_t delay_stage_config = neuron_delay_stage_config[d];
        if (nonempty_bit_field(delay_stage_config, neuron_bit_field_words)) {

            // Get key mask for this delay stage and it's time slot
            uint32_t delay_stage_delay = (d + 1) * DELAY_STAGE_LENGTH;
            uint32_t delay_stage_time_slot =
                ((time - delay_stage_delay) & num_delay_slots_mask);
            uint8_t *delay_stage_spike_counters =
                spike_counters[delay_stage_time_slot];

            log_debug("%u: Checking time slot %u for delay stage %u",
                      time, delay_stage_time_slot, d);

            // Loop through neurons
            for (uint32_t n = 0; n < num_neurons; n++) {

                // If this neuron emits a spike after this stage
                if (bit_field_test(delay_stage_config, n)) {

                    // Calculate key all spikes coming from this neuron will be
                    // sent with
                    uint32_t spike_key = ((d * num_neurons) + n) + key;

                    if (delay_stage_spike_counters[n] > 0) {
                        log_debug("Neuron %u sending %u spikes after delay"
                                  "stage %u with key %x",
                                  n, delay_stage_spike_counters[n], d,
                                  spike_key);
                    }

                    // Loop through counted spikes and send
                    for (uint32_t s = 0; s < delay_stage_spike_counters[n];
                            s++) {
                        while (!spin1_send_mc_packet(spike_key, 0,
                                                     NO_PAYLOAD)) {
                            spin1_delay_us(1);
                        }
                        n_spikes_sent += 1;

                    }
                }

                // Wait until the expected time to send
                while (tc[T1_COUNT] > expected_time) {

                    // Do Nothing
                    n_delays += 1;
                }
                expected_time -= time_between_spikes;
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
        rt_error(RTE_SWERR);
    }

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Initialise the incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(256)) {
         rt_error(RTE_SWERR);
    }

    // Set timer tick (in microseconds)
    log_info("Timer period %u", timer_period);
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(MC_PACKET_RECEIVED, incoming_spike_callback, MC_PACKET);
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER);

    simulation_run();
}
