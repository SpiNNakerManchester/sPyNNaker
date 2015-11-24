/*! \file
 *
 *  \brief utility class which ensures that format of spikes being recorded is
 *   done in a standard way
 *
 *
 *  \details The API includes:
 *     - out_spikes_reset
 *          clears the memory used as a tracker for the next set of spikes
 *          which will be recorded to SDRAM at some point
 *     - out_spikes_initialize
 *          initialises a piece of memory which can contain a flag to say if
 *          any source has spiked between resets
 *     - out_spikes_record
 *          records the current set of flags for each spike source into the
 *          spike recording region in SDRAM (flags to deduce which regions are
 *           active are handed to this method due to recording not containing
 *           them itself). TODO change the recording.h and recording.c to
 *           contain the channels itself.
 *     - out_spikes_is_empty
 *          helper method which checks if the current spikes flags have any
 *          recorded for use.
 *     - out_spikes_is_spike
 *          helper method which checks if a given source has spiked since the
 *           last reset.
 *     - out_spikes_print
 *          a debug function that when the model is compiled in DEBUG mode will
            record into SDRAM the spikes that are currently been recorded as
            having spiked since the last reset command
 *     - out_spikes_set_spike
 *          helper method which allows models to state that a given spike source
            has spiked since the last reset.
 */

#ifndef _OUT_SPIKES_H_
#define _OUT_SPIKES_H_

#include "neuron-typedefs.h"

#include <bit_field.h>

extern bit_field_t out_spikes;

//! \brief clears the memory used as a tracker for the next set of spikes
//! which will be recorded to SDRAM at some point
//! \return None
void out_spikes_reset();

//! \brief initialises a piece of memory which can contain a flag to say if
//! any source has spiked between resets
//! \param[in] max_spike_sources the max number of sources which can be
//! expected to spike between resets
//! \return a boolean which is True if the initialisation was successful,
//! false otherwise
bool out_spikes_initialize(size_t max_spike_sources);

//! \brief records the current set of flags for each spike source into the
//! spike recording region in SDRAM (flags to deduce which regions are active
//! are handed to this method due to recording not containing them itself).
//! TODO change the recording.h and recording.c to contain the channels itself.
//! \param[in] channel the channel to record to
//! \param[in] time the time of the recording
//! \return None
void out_spikes_record(uint8_t channel, uint32_t time);

//! \brief helper method which checks if the current spikes flags have any
//! recorded for use.
//! \return boolean which is true if there are no recorded spikes since the
//! last reset and false otherwise.
bool out_spikes_is_empty();

//! \brief helper method which checks if a given source has spiked since the
//! last reset.
//! \param[in] spike_source_index the index of the spike source to check if it
//! has spiked since the last reset.
//! \return boolean which is true if the spike source has spiked since the last
//! reset command
bool out_spikes_is_spike(index_t spike_source_index);

//! \brief a debug function that when the model is compiled in DEBUG mode will
//! record into SDRAM the spikes that are currently been recorded as having
//! spiked since the last reset command
//! \return nothing
void out_spikes_print();

//! \brief helper method which allows models to state that a given spike source
//! has spiked since the last reset.
//! \param[in] spike_source_index the index of the spike source which has
//! spiked.
//! \return None
static inline void out_spikes_set_spike(index_t spike_source_index) {
    bit_field_set(out_spikes, spike_source_index);
}

#endif // _OUT_SPIKES_H_
