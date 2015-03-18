#ifndef _RECORDING_H_
#define _RECORDING_H_

/*
 * TODO need to change the interface so that we add channels to recording which
 * then keeps it in a dynamic list so that models don't need to keep track of
 * the recording channels themselves.
 */


#include "neuron-typedefs.h"

typedef enum recording_channel_e {
    e_recording_channel_spike_history,
    e_recording_channel_neuron_potential,
    e_recording_channel_neuron_gsyn,
    e_recording_channel_max,
} recording_channel_e;

#define RECORDING_POSITION_IN_REGION 3

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

//! \brief Determines if the given channel has been initialised yet.
//! \param[in] recording_flags The flags as read by recording_read_region_sizes.
//! \param[in] channel The channel to check for already been initialised.
//! \return True if the channel has already been initialised, False otherwise.
bool recording_is_channel_enabled(uint32_t recording_flags,
        recording_channel_e channel);

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
        uint32_t size_bytes);

//! \brief records some data into a specific recording channel.
//! \param[in] channel the channel to store the data into.
//! \param[in] data the data to store into the channel.
//! \param[in] size_bytes the number of bytes that this data will take up.
//! \return boolean which is True if the data has been stored in the channel,
//! False otherwise.
bool recording_record(
        recording_channel_e channel, void *data, uint32_t size_bytes);

//! \brief updated the first word in the recording channel's memory region with
//! the number of bytes that was actually written to SDRAM and then closes the
//! channel so that future records fail.
//! \return nothing
void recording_finalise();

#endif // _RECORDING_H_
