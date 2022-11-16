/*
 * Copyright (c) 2021 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef __SEND_MC_H__
#define __SEND_MC_H__

#include <stdint.h>
#include <spin1_api.h>
#include <spin1_api_params.h>
#include <debug.h>

//! Mask to recognise the Comms Controller "not full" flag
#define TX_NOT_FULL_MASK 0x10000000

//! \brief wait for the comms controller to be ready to send.
//!        Note that this will RTE if it isn't ready by a certain time
static inline void wait_for_cc(void) {
    uint32_t n_loops = 0;
    while (!(cc[CC_TCR] & TX_NOT_FULL_MASK) && (n_loops < 10000)) {
        spin1_delay_us(1);
        n_loops++;
    }
    if (!(cc[CC_TCR] & TX_NOT_FULL_MASK)) {
        log_error("Couldn't send spike; TCR=0x%08x\n", cc[CC_TCR]);
        rt_error(RTE_SWERR);
    }
}

//! \brief Perform direct spike sending with hardware for speed
//! \param[in] key The key to send
static inline void send_spike_mc(uint32_t key) {
	wait_for_cc();
    cc[CC_TCR] = PKT_MC;
    cc[CC_TXKEY]  = key;
}

//! \brief Perform direct spike-with-payload sending with hardware for speed
//! \param[in] key The key to send
static inline void send_spike_mc_payload(uint32_t key, uint32_t payload) {
    wait_for_cc();
    cc[CC_TCR] = PKT_MC;
    cc[CC_TXDATA] = payload;
    cc[CC_TXKEY]  = key;
}
#endif // __SEND_MC_H__
