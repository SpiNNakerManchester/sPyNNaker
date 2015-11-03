/*! \file
 *
 *  \brief the implementation of the out_spikes.h interface.
 */

#include "out_spikes.h"
#include "recording.h"

#include <debug.h>

// Globals
typedef struct timed_out_spikes{
    uint32_t time;
    uint32_t out_spikes[16];
}timed_out_spikes;

timed_out_spikes spikes;
bit_field_t out_spikes;

static size_t out_spikes_size;


//! \brief clears the memory used as a tracker for the next set of spikes
//! which will be recorded to SDRAM at some point
//! \return None
void out_spikes_reset() {
    clear_bit_field(out_spikes, out_spikes_size);
}

//! \brief initialises a piece of memory which can contain a flag to say if
//! any source has spiked between resets
//! \param[in] max_spike_sources the max number of sources which can be
//! expected to spike between resets
//! \return a boolean which is True if the initialisation was successful,
//! false otherwise
bool out_spikes_initialize(size_t max_spike_sources) {
    out_spikes_size = get_bit_field_size(max_spike_sources);
    log_info("Out spike size is %u words, allowing %u spike sources",
             out_spikes_size, max_spike_sources);
    out_spikes = spikes.out_spikes;
/*
    out_spikes = (bit_field_t) sark_alloc(
        out_spikes_size * sizeof(uint32_t), 1);
    if (out_spikes == NULL) {
        log_error("Could not allocate out spikes array");
        return false;
    }
*/
    clear_bit_field(out_spikes, 16);
    out_spikes_reset();
    return true;
}

//! \brief records the current set of flags for each spike source into the
//! spike recording region in SDRAM (flags to deduce which regions are active
//! are handed to this method due to recording not containing them itself).
//! TODO change the recording.h and recording.c to contain the channels itself.
//! \param[in] recording_flags the recording flags which state which region
//! channels are being used.
//! \return None
void out_spikes_record(uint32_t recording_flags, uint32_t time) {

    // If we should record the spike history, copy out-spikes to the
    // appropriate recording channel
    if (recording_is_channel_enabled(
            recording_flags, e_recording_channel_spike_history)) {
        spikes.time = time;
        recording_record(
            e_recording_channel_spike_history, &spikes,
            (out_spikes_size + 1) * sizeof(uint32_t));
    }
}

//! \brief helper method which checks if the current spikes flags have any
//! recorded for use.
//! \return boolean which is true if there are no recorded spikes since the
//! last reset and false otherwise.
bool out_spikes_is_empty() {
    return (empty_bit_field(out_spikes, out_spikes_size));

}

//! \brief helper method which checks if a given source has spiked since the
//! last reset.
//! \param[in] spike_source_index the index of the spike source to check if it
//! has spiked since the last reset.
//! \return boolean which is true if the spike source has spiked since the last
//! reset command
bool out_spikes_is_spike(index_t neuron_index) {
    return (bit_field_test(out_spikes, neuron_index));
}

//! \brief a debug function that when the model is compiled in DEBUG mode will
//! record into SDRAM the spikes that are currently been recorded as having
//! spiked since the last reset command
//! \return nothing
void out_spikes_print() {
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("out_spikes:\n");

    if (!out_spikes_is_empty()) {
        log_debug("-----------\n");
        print_bit_field(out_spikes, out_spikes_size);
        log_debug("-----------\n");
    }
#endif // LOG_LEVEL >= LOG_DEBUG
}
