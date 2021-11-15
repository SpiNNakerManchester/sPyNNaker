/*
 * Copyright (c) 2019-2020 The University of Manchester
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

//! \file
//! \brief Implementation of direct_synapses.h
#include <debug.h>
#include <spin1_api.h>
#include <common/neuron-typedefs.h>

//! \brief The type of a singleton synaptic row.
//! \details The counts are constant. See ::synapse_row_plastic_part_t and
//!     ::synapse_row_fixed_part_t for what this is a packed version of.
typedef struct single_synaptic_row_t {
    const uint32_t n_plastic;   //!< Number of plastic synapses. Always zero
    const uint32_t n_fixed;     //!< Number of fixed synapses. Always one
    const uint32_t n_plastic_controls; //!< Number of plastic controls. Always zero
    uint32_t synapse_datum;     //!< The value of the single synapse
} single_synaptic_row_t;

//! Working buffer for direct synapse access
static single_synaptic_row_t single_fixed_synapse = {0, 1, 0, 0};

//! The layout of the direct matrix region
typedef struct {
    const uint32_t size;        //!< Size of data, _not_ number of elements
    const uint32_t data[];      //!< Direct matrix data
} direct_matrix_data_t;

bool direct_synapses_initialise(
        void *direct_matrix_address, address_t *direct_synapses_address) {
    direct_matrix_data_t *direct_matrix = direct_matrix_address;
    // Work out the positions of the direct and indirect synaptic matrices
    // and copy the direct matrix to DTCM
    uint32_t direct_matrix_size = direct_matrix->size;
    log_debug("Direct matrix malloc size is %d", direct_matrix_size);

    if (direct_matrix_size != 0) {
        void *dtcm_copy = spin1_malloc(direct_matrix_size);
        if (dtcm_copy == NULL) {
            log_error("Not enough memory to allocate direct matrix");
            return false;
        }
        log_debug("Copying %u bytes of direct synapses to 0x%08x",
                direct_matrix_size, dtcm_copy);
        spin1_memcpy(dtcm_copy, direct_matrix->data, direct_matrix_size);
        *direct_synapses_address = dtcm_copy;
    }

    return true;
}

synaptic_row_t direct_synapses_get_direct_synapse(void *row_address) {
    uint32_t *data = row_address;
    single_fixed_synapse.synapse_datum = *data;
    return (synaptic_row_t) &single_fixed_synapse;
}
