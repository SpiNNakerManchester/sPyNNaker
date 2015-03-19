/*! \file
 *
 *  \brief implementation of recording.h
 *
 */

#include "recording.h"

// Standard includes
#include <string.h>
#include <debug.h>

//---------------------------------------
// Structures
//---------------------------------------
//! structure that defines a channel in memory.
typedef struct recording_channel_t {
    address_t counter;
    uint8_t *start;
    uint8_t *current;
    uint8_t *end;
} recording_channel_t;

//! positions within the recording region definition for each type of event
//! Available to be recorded
typedef enum recording_positions {
    flags_for_recording, spikes_position, protential_position, gsyn_position,
} recording_positions;



//---------------------------------------
// Globals
//---------------------------------------
//! array containing all possible channels.
static recording_channel_t g_recording_channels[e_recording_channel_max];

//---------------------------------------
// Private method
//---------------------------------------
//! \brief checks that a channel has been initialised or is still awaiting
//! initialisation
//! \param[in] channel the channel strut which represents the memory data for a
//! given recording region
//! \return boolean which is True if the channel has been initialised or false
//! otherwise
static inline bool has_been_initialsed(recording_channel_e channel) {
    return (g_recording_channels[channel].start != NULL
            && g_recording_channels[channel].end != NULL);
}

//----------------------------------------
//  Private method
//----------------------------------------
//! \brief closes a channel so that future records fail as the channel has
//! been closed
//! \param[in] channel the channel strut which represents the memory data for a
//! given recording region, which is to be closed.
//! \return boolean which is True is the channel was successfully closed and
//! False otherwise.
static inline bool close_channel(recording_channel_e channel) {
	g_recording_channels[channel].start = NULL;
	g_recording_channels[channel].end = NULL;
	return true;
}

//---------------------------------------
// Public API
//---------------------------------------
//! \checks if a channel is expected to be producing recordings.
//! \param[in] recording_flags the integer which contains the flags for the
//! if an channel is enabled.
//! \param[in] channel the channel strut which contains the memory data for a
//! given channel
//! \return boolean which is True if the channel is expected to produce
//! recordings or false otherwise
bool recording_is_channel_enabled(uint32_t recording_flags,
        recording_channel_e channel) {
    return (recording_flags & (1 << channel)) != 0;
}

//! \extracts the sizes of the recorded regions from SDRAM
//! \param[in] region_start the absolute address in SDRAM
//! \param[in] recording_flags the flag ids read from SDRAM
//! \param[out] spike_history_region_size if this region is set to have
//! data recorded into it, it will get set with the size of the spike
//! recorder region
//! \param[out] neuron_potential_region_size if this region is set to have
//! data recorded into it, it will get set with the size of the potential
//! recorder region
//! \param[out] neuron_gysn_region_size
//! \return This method does not return anything
void recording_read_region_sizes(
        address_t region_start, uint32_t* recording_flags,
        uint32_t* spike_history_region_size,
        uint32_t* neuron_potential_region_size,
        uint32_t* neuron_gysn_region_size) {
    *recording_flags = region_start[flags_for_recording];
    if (recording_is_channel_enabled(*recording_flags,
                e_recording_channel_spike_history)
            && (spike_history_region_size != NULL)) {
        *spike_history_region_size = region_start[spikes_position];
    }
    if (recording_is_channel_enabled(*recording_flags,
                e_recording_channel_neuron_potential)
            && (neuron_potential_region_size != NULL)) {
        *neuron_potential_region_size = region_start[protential_position];
    }
    if (recording_is_channel_enabled(*recording_flags,
                e_recording_channel_neuron_gsyn)
            && (neuron_gysn_region_size != NULL)) {
        *neuron_gysn_region_size = region_start[gsyn_position];
    }
}

//! \brief initialises a channel with the start, end, size and current position
//! in SDRAM for the channel handed in.
//! \param[in] output_region the absolute memory address in SDRAM for the
//!recording region
//! \param[out] channel the channel to which we are initialising the
//! parameters of.
// \param[out] size_bytes the size of memory that the channel can put data into
//! \return boolean which is True if the channel was successfully initialised
//! or False otherwise.
bool recording_initialse_channel(
        address_t output_region, recording_channel_e channel,
        uint32_t size_bytes) {

    if (has_been_initialsed(channel)) {
        log_error("Recording channel %u already configured", channel);

        // CHANNEL already initialised
        return false;
    } else {
        recording_channel_t *recording_channel = &g_recording_channels[channel];

        // Cache pointer to output counter in recording channel and set it to 0
        recording_channel->counter = &output_region[0];
        *recording_channel->counter = 0;

        // Calculate pointers to the start, current position and end of this
        // memory block
        recording_channel->start = (uint8_t*) &output_region[1];
        recording_channel->current = (uint8_t*) &output_region[1];
        recording_channel->end = recording_channel->start + size_bytes;

        log_info("Recording channel %u configured to use %u byte memory block"
                 " starting at %08x", channel, size_bytes,
                 recording_channel->start);
        return true;
    }
}

//! \brief records some data into a specific recording channel.
//! \param[in] channel the channel to store the data into.
//! \param[in] data the data to store into the channel.
//! \param[in] size_bytes the number of bytes that this data will take up.
//! \return boolean which is True if the data has been stored in the channel,
//! False otherwise.
bool recording_record(
        recording_channel_e channel, void *data, uint32_t size_bytes) {
    if (has_been_initialsed(channel)) {
        recording_channel_t *recording_channel = &g_recording_channels[channel];

        // If there's space to record
        if (recording_channel->current
                < (recording_channel->end - size_bytes)) {
            // Copy data into recording channel
            memcpy(recording_channel->current, data, size_bytes);

            // Update current pointer
            recording_channel->current += size_bytes;
            return true;
        } else {
            log_info("ERROR: recording channel %u out of space", channel);
            return false;
        }
    } else {
        log_info("ERROR: recording channel %u not in use", channel);

        return false;
    }

}

//! \brief updated the first word in the recording channel's memory region with
//! the number of bytes that was actually written to SDRAM and then closes the
//! channel so that future records fail.
//! \return nothing
void recording_finalise() {
    log_info("Finalising recording channels");

    // Loop through channels
    for (uint32_t channel = 0; channel < e_recording_channel_max; channel++) {
        // If this channel's in use
        if (has_been_initialsed(channel)) {
            recording_channel_t *recording_channel =
                &g_recording_channels[channel];

            // Calculate the number of bytes that have been written and write
            // back to SDRAM counter
            uint32_t num_bytes_written = recording_channel->current
                                         - recording_channel->start;
            log_info(
                "\tFinalising channel %u - %x bytes of data starting at %08x",
                channel, num_bytes_written + sizeof(uint32_t),
                recording_channel->counter);
            *recording_channel->counter = num_bytes_written;
            if(!close_channel(channel)){
            	log_error("could not close channel %u.", channel);
            }
            else{
            	log_info("closed channel %u.", channel);
            }
        }
        else{
        	log_error("channel %u is already closed.", channel);
        }
    }
}
