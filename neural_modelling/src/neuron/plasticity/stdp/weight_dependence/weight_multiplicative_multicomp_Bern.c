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

#include "weight_multiplicative_multicomp_Bern.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t *plasticity_weight_region_data;
uint32_t *weight_shift;

//---------------------------------------
// Functions
//---------------------------------------
uint32_t *weight_initialise(
        uint32_t *address, uint32_t n_synapse_types,
        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    io_printf(IO_BUF, "weight_initialise: starting \n");
    io_printf(IO_BUF, "\tmultiplicative Bern weight dependence \n");

    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    plasticity_weight_region_data =
            spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);
    if (plasticity_weight_region_data == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }
    weight_shift =
            spin1_malloc(sizeof(uint32_t) * n_synapse_types);
    if (weight_shift == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }

    int32_t *plasticity_word = (int32_t *) address;
    for (uint32_t s = 0; s < n_synapse_types; s++) {
        // Copy parameters
        plasticity_weight_region_data[s].min_weight = *plasticity_word++;
        plasticity_weight_region_data[s].max_weight = *plasticity_word++;

        spin1_memcpy(&plasticity_weight_region_data[s].learning_rate, plasticity_word, sizeof(REAL));

        plasticity_word++;

        weight_shift[s] = ring_buffer_to_input_buffer_left_shifts[s];

        log_debug("\tSynapse type %u: Min weight:%d, Max weight:%d, learning rate:%d,"
                " Weight shift:%u",
                s, plasticity_weight_region_data[s].min_weight,
                plasticity_weight_region_data[s].max_weight,
                plasticity_weight_region_data[s].learning_rate,
                weight_shift[s]);
    }

    log_debug("weight_initialise: completed successfully");

    // Return end address of region
    return (address_t) plasticity_word;
}