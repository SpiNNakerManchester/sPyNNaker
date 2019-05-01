#ifndef _SPIKE_PROCESSING_H_
#define _SPIKE_PROCESSING_H_

#include <common/neuron-typedefs.h>
#include <common/in_spikes.h>
#include <spin1_api.h>

bool spike_processing_initialise(
    size_t row_max_n_bytes, uint mc_packet_callback_priority,
    uint user_event_priority, uint incoming_spike_buffer_size);

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t spike_processing_get_buffer_overflows();

//! \brief get the address of the circular buffer used for buffering received
//! spikes before processing them
//! \return address of circular buffer
circular_buffer get_circular_buffer();

//! \brief set the number of times spike_processing has to attempt rewiring
//! \return bool: currently, always true
bool spike_processing_do_rewiring(int number_of_rew);

//! \brief has this core received any spikes since the last batch of rewires?
//! \return bool
bool received_any_spike();

#endif // _SPIKE_PROCESSING_H_
