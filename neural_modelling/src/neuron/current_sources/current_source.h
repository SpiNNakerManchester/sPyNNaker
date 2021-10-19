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
//! \brief Current source implementations
//! \file
//! \brief General API of a current source implementation
#ifndef _CURRENT_SOURCE_H_
#define _CURRENT_SOURCE_H_

#include <common/neuron-typedefs.h>

// Not sure if this is needed or not when initialising...
//static void current_source_initialise_counters(void);

//! \brief Initialise the particular implementation of the data
//! \param[in] cs_address: The address to start reading data from
//! \return True if successful
static bool current_source_impl_initialise(address_t cs_address);

static bool current_source_impl_load_parameters(address_t cs_address);

static REAL current_source_get_offset(uint32_t time, uint32_t neuron_index);

#endif // _CURRENT_SOURCE_H_
