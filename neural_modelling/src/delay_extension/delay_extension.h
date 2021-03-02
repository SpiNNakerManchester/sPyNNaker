/*
 * Copyright (c) 2017-2019 The University of Manchester
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

//! \dir
//! \brief Delay Extension Process
//! \file
//! \brief Declarations for delay extensions

#ifndef __DELAY_EXTENSION_H__
#define __DELAY_EXTENSION_H__

#include <common-typedefs.h>

//! region identifiers
typedef enum region_identifiers {
    //! General simulation system control
    SYSTEM = 0,
    //! Delay parameters (see delay_parameters)
    DELAY_PARAMS = 1,
    //! Provenance recording region
    PROVENANCE_REGION = 2,
    //! On-chip delay matrix expansion region
    EXPANDER_REGION = 3,
    //! tdma data
    TDMA_REGION = 4,
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
    uint32_t delay_blocks[];      //!< Descriptions of delays to apply
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
