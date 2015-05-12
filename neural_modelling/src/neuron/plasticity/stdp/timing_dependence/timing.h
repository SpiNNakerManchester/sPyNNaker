#ifndef _TIMING_H_
#define _TIMING_H_

#include "../synapse_structure/synapse_structure.h"

//! \brief the initialiser for the time deppendence which checks the
//!        correct component was compiled in and the data is well formed in
//!        SDRAM
//! \param[in] address The SDRAM address where the timing params are stored
//! \param[in] timing_magic_number the magic number which represents the
//!            timing component being compiled in.
//! \return a address pram which is NULL if the init failed, or the
//!  the end of the timing region as an absolute SDRAM memory address,
address_t timing_initialise(address_t address, uint32_t timing_magic_number);

static post_trace_t timing_get_initial_post_trace();

static post_trace_t timing_add_post_spike(uint32_t time, uint32_t last_time,
                                          post_trace_t last_trace);

static pre_trace_t timing_add_pre_spike(uint32_t time, uint32_t last_time,
                                        pre_trace_t last_trace);

static update_state_t timing_apply_pre_spike(
    uint32_t time, pre_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace,  uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state);

static update_state_t timing_apply_post_spike(
    uint32_t time, post_trace_t trace, uint32_t last_pre_time,
    pre_trace_t last_pre_trace, uint32_t last_post_time,
    post_trace_t last_post_trace, update_state_t previous_state);

#endif // _TIMING_H_
