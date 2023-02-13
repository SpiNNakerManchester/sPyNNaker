/*
 * Copyright (c) 2020-2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef _DMA_COMMON_H_
#define _DMA_COMMON_H_
#include <spin1_api.h>
#include <spin1_api_params.h>
#include <stdbool.h>

//! Value of the masked DMA status register when transfer is complete
#define DMA_COMPLETE 0x400

//! Mask to apply to the DMA status register to check for completion
#define DMA_CHECK_MASK 0x401

//! DMA write flags
static const uint32_t DMA_WRITE_FLAGS =
        DMA_WIDTH << 24 | DMA_BURST_SIZE << 21 | DMA_WRITE << 19;

//! DMA read flags
static const uint32_t DMA_READ_FLAGS =
        DMA_WIDTH << 24 | DMA_BURST_SIZE << 21 | DMA_READ << 19;

//! \brief Is there a DMA currently running?
//! \return True if there is something transferring now.
static inline bool dma_done(void) {
    return (dma[DMA_STAT] & DMA_CHECK_MASK) == DMA_COMPLETE;
}

//! \brief Start the DMA doing a write; the write may not be finished at the
//!        end of this call.
//! \param[in] tcm_address: The local DTCM address to read the data from
//! \param[in] system_address: The SDRAM address to write the data to
//! \param[in] n_bytes: The number of bytes to be written from DTCM to SDRAM
static inline void do_fast_dma_write(void *tcm_address, void *system_address,
        uint32_t n_bytes) {
#if LOG_LEVEL >= LOG_DEBUG
    // Useful for checking when things are going wrong, but shouldn't be
    // needed in normal code
    uint32_t stat = dma[DMA_STAT];
    if (stat & 0x1FFFFF) {
        log_error("DMA pending or in progress on write: 0x%08x", stat);
        rt_error(RTE_SWERR);
    }
#endif
    uint32_t desc = DMA_WRITE_FLAGS | n_bytes;
    dma[DMA_ADRS] = (uint32_t) system_address;
    dma[DMA_ADRT] = (uint32_t) tcm_address;
    dma[DMA_DESC] = desc;
}

//! \brief Start the DMA doing a read; the read may not be finished at the end
//!        of this call.
//! \param[in] system_address: The SDRAM address to read the data from
//! \param[in] tcm_address: The DTCM address to write the data to
//! \param[in] n_bytes: The number of bytes to be read from SDRAM to DTCM
static inline void do_fast_dma_read(void *system_address, void *tcm_address,
        uint32_t n_bytes) {
#if LOG_LEVEL >= LOG_DEBUG
    // Useful for checking when things are going wrong, but shouldn't be
    // needed in normal code
    uint32_t stat = dma[DMA_STAT];
    if (stat & 0x1FFFFF) {
        log_error("DMA pending or in progress on read: 0x%08x", stat);
        rt_error(RTE_SWERR);
    }
#endif
    uint32_t desc = DMA_READ_FLAGS | n_bytes;
    dma[DMA_ADRS] = (uint32_t) system_address;
    dma[DMA_ADRT] = (uint32_t) tcm_address;
    dma[DMA_DESC] = desc;
}

//! \brief Wait for a DMA transfer to complete.
static inline void wait_for_dma_to_complete(void) {
#if LOG_LEVEL >= LOG_DEBUG
    // Useful for checking when things are going wrong, but shouldn't be
    // needed in normal code
    uint32_t n_loops = 0;
    while (!dma_done() && n_loops < 10000) {
        n_loops++;
    }
    if (!dma_done()) {
        log_error("Timeout on DMA loop: DMA stat = 0x%08x!", dma[DMA_STAT]);
        rt_error(RTE_SWERR);
    }
#else
    // This is the normal loop, done without checking
    while (!dma_done()) {
        continue;
    }
#endif
    dma[DMA_CTRL] = 0x8;
}


//! \brief Cancel any outstanding DMA transfers
static inline void cancel_dmas(void) {
    dma[DMA_CTRL] = 0x3F;
    while (dma[DMA_STAT] & 0x1) {
        continue;
    }
    dma[DMA_CTRL] = 0xD;
    while (dma[DMA_CTRL] & 0xD) {
        continue;
    }
}

#endif
