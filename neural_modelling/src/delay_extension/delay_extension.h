/*
 * Copyright (c) 2017 The University of Manchester
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

//! \dir
//! \brief Delay Extension Process
//! \file
//! \brief Declarations for delay extensions

#ifndef __DELAY_EXTENSION_H__
#define __DELAY_EXTENSION_H__

#include <common-typedefs.h>

//! Constants
#define DELAY_STAGE_LENGTH  64

//! region identifiers
typedef enum region_identifiers {
    //! General simulation system control
    SYSTEM = 0,
    //! Delay parameters (see delay_parameters)
    DELAY_PARAMS = 1,
    //! Provenance recording region
    PROVENANCE_REGION = 2,
    //! tdma data
    TDMA_REGION = 3,
} region_identifiers;

//! \brief Delay configuration, as read from SDRAM where it was placed by DSG
//! or by on-chip generation
struct delay_parameters {
    uint32_t has_key;             //!< bool for if this vertex has a key.
    uint32_t key;                 //!< Key to use for sending messages
    uint32_t incoming_key;        //!< Key to accept messages with
    uint32_t incoming_mask;       //!< Mask to filter delay_parameters::incoming_key
    uint32_t n_atoms;             //!< Number of atoms
    uint32_t n_delay_stages;      //!< Number of delay stages
    uint32_t n_delay_in_a_stage;  //!< Number of delays in a given stage
    uint32_t clear_packets;       //!< Clear packets each timestep?
    uint32_t n_colour_bits;       //!< The number of bits used for colour
};

//! \brief Encode a delay as a 16-bit integer
//! \param[in] index: the index within the stage (uint8_t)
//! \param[in] stage: the stage of the delay (uint8_t)
//! \return The encoded value (uint16_t)
#define pack_delay_index_stage(index, stage) \
    ((index & 0xFF) | ((stage & 0xFF) << 8))

//! \brief Decode a delay index (encoded with pack_delay_index_stage())
//! \param[in] packed: the encoded value
//! \return The delay index
#define unpack_delay_index(packed)      (packed & 0xFF)

//! \brief Decode a delay stage (encoded with pack_delay_index_stage())
//! \param[in] packed: the encoded value
//! \return The delay stage
#define unpack_delay_stage(packed)      ((packed >> 8) & 0xFF)

#endif // __DELAY_EXTENSION_H__
