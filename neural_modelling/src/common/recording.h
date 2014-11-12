#ifndef _RECORDING_H_
#define _RECORDING_H_

#include "neuron-typedefs.h"

typedef enum recording_channel_e {
    e_recording_channel_spike_history,
    e_recording_channel_neuron_potential,
    e_recording_channel_neuron_gsyn,
    e_recording_channel_max,
} recording_channel_e;

//! \brief Reads the size of the recording regions - pass 0s for the region
//!        size pointer when the value is not needed
//!
//! The region is expected to be formatted as:
//!      - 32-bit word with last 3-bits indicating if each of the 3 regions are
//!        in use
//!      - 32-bit word for the size of the spike history region
//!      - Optional 32-bit word for the size of the potential region (must be
//!        present if the gsyn region size is present).
//!      - Optional 32-bit word for the size of the gsyn region
//!
//! \param[in]  region_start A pointer to the start of the region (or to the
//!                          first 32-bit word if included as part of another
//!                          region
//! \param[out] recording_flags A pointer to an integer to receive the flags
//! \param[out] spike_history_region_size A pointer to an in integer to receive
//!                                       the size of the spike history region.
//! \param[out] neuron_potential_region_size A pointer to an in integer to
//!                                          receive the size of the neuron
//!                                          potential region.
//! \param[out] neuron_gsyn_region_size A pointer to an in integer to receive
//!                                     the size of the neuron gsyn region.
void recording_read_region_sizes(
        address_t region_start, uint32_t* recording_flags,
        uint32_t* spike_history_region_size,
        uint32_t* neuron_potential_region_size,
        uint32_t* neuron_gysn_region_size);

//! \brief Determines if the given channel is marked as enabled in the flags
//!
//! \param recording_flags The flags as read by recording_read_region_sizes
//! \param channel The channel to test for
//! \return True if the channel is marked as enabled, False otherwise
bool recording_is_channel_enabled(uint32_t recording_flags,
        recording_channel_e channel);

bool recording_initialze_channel(
        address_t output_region, recording_channel_e channel,
        uint32_t size_bytes);

bool recording_record(
        recording_channel_e channel, void *data, uint32_t size_bytes);

void recording_finalise();

#endif // _RECORDING_H_
