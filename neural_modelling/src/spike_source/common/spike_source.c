#include "spike_source_impl.h"

#include "../../common/recording.h"

#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <string.h>

// Globals
uint32_t spike_source_key = 0;
uint32_t spike_source_n_sources = 0;

static uint32_t recording_flags = 0;
static uint32_t time;
static uint32_t simulation_ticks = 0;

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
            spike_source_impl_get_application_id(),
            timer_period, &simulation_ticks)) {
        return false;
    }

    // Get the recording information
    uint32_t spike_history_region =
            spike_source_impl_get_spike_recording_region_id();
    uint32_t spike_history_region_size;
    recording_read_region_sizes(
            &data_specification_get_region(0, address)[3], &recording_flags,
            &spike_history_region_size, NULL, NULL);
    if (recording_is_channel_enabled(
            recording_flags, e_recording_channel_spike_history)) {
        recording_initialze_channel(
                data_specification_get_region(spike_history_region, address),
                e_recording_channel_spike_history, spike_history_region_size);
    }

    // Initialize
    if (!spike_source_impl_initialize(address, &spike_source_key,
            &spike_source_n_sources)) {
        return false;
    }

    log_info("initialize: completed successfully");

    return true;
}

// Callbacks
void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    time++;

    log_info("Timer tick %u", time);

    // If a fixed number of simulation ticks are specified and these have passed
    if (simulation_ticks != UINT32_MAX && time >= simulation_ticks) {
        log_info("Simulation complete.\n");

        // Finalise any recordings that are in progress, writing back the final
        // amounts of samples recorded to SDRAM
        recording_finalise();
        spin1_exit(0);
    }

    // Generate spikes
    spike_source_impl_generate_spikes(time);

    // Record output spikes if required
    out_spikes_record(recording_flags);

    if (out_spikes_is_nonempty()) {
        out_spikes_print();

        for (index_t i = 0; i < spike_source_n_sources; i++) {
            if (out_spikes_is_spike(i)){
                log_debug("Sending spike packet %x", spike_source_key | i);
                spin1_send_mc_packet(spike_source_key | i, 0, NO_PAYLOAD);
                spin1_delay_us(1);
            }
        }

        out_spikes_reset();
    }
}

// Entry point
void c_main(void) {

    // Load DTCM data
    uint32_t timer_period;
    initialize(&timer_period);

    // Start the time at "-1" so that the first tick will be 0
    time = UINT32_MAX;

    // Initialize out spikes buffer to support number of neurons
    out_spikes_initialize(spike_source_n_sources);

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Register callbacks
    spin1_callback_on(TIMER_TICK, timer_callback, 2);
    spin1_callback_on(DMA_TRANSFER_DONE, spike_source_impl_dma_callback, 0);

    log_info("Starting");
    simulation_run();
}
