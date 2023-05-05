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

#include "weight_eprop_reg_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
// Global plasticity parameter data
plasticity_weight_region_data_t *plasticity_weight_region_data;

uint32_t *weight_shift;

//! \brief How the configuration data for additive_one_term is laid out in
//!     SDRAM. The layout is an array of these.
typedef struct {
    accum min_weight;
    accum max_weight;
    accum a2_plus;
    accum a2_minus;
    accum reg_rate;
} eprop_one_term_config_t;

//---------------------------------------
// Functions
//---------------------------------------
address_t weight_initialise(
        address_t address, uint32_t n_synapse_types,
        UNUSED uint32_t *ring_buffer_to_input_buffer_left_shifts) {
    // Copy plasticity region data from address
    // **NOTE** this seems somewhat safer than relying on sizeof
    eprop_one_term_config_t *config = (eprop_one_term_config_t *) address;

    plasticity_weight_region_data_t *dtcm_copy = plasticity_weight_region_data =
            spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);
    if (dtcm_copy == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }

    weight_shift = spin1_malloc(sizeof(uint32_t) * n_synapse_types);
    if (weight_shift == NULL) {
        log_error("Could not initialise weight region data");
        return NULL;
    }

    for (uint32_t s = 0; s < n_synapse_types; s++, config++) {
        dtcm_copy[s].min_weight = config->min_weight;
        dtcm_copy[s].max_weight = config->max_weight;
        dtcm_copy[s].a2_plus = config->a2_plus;
        dtcm_copy[s].a2_minus = config->a2_minus;
        dtcm_copy[s].reg_rate = config->reg_rate;

        // Copy weight shift
        weight_shift[s] = ring_buffer_to_input_buffer_left_shifts[s];

        log_debug("\tSynapse type %u: Min weight:%k, Max weight:%k, A2+:%k, A2-:%k reg_rate:%k",
                s, dtcm_copy[s].min_weight, dtcm_copy[s].max_weight,
                dtcm_copy[s].a2_plus, dtcm_copy[s].a2_minus,
				dtcm_copy[s].reg_rate);
    }

    // Return end address of region
    return (address_t) config;
}

////---------------------------------------
//// Functions
////---------------------------------------
//address_t weight_initialise(
//        address_t address, uint32_t n_synapse_types,
//        uint32_t *ring_buffer_to_input_buffer_left_shifts) {
//    use(ring_buffer_to_input_buffer_left_shifts);
//
//    io_printf(IO_BUF, "weight_initialise: starting\n");
//    io_printf(IO_BUF, "\teprop_reg weight dependence\n");
//
//    // Copy plasticity region data from address
//    // **NOTE** this seems somewhat safer than relying on sizeof
//    int32_t *plasticity_word = (int32_t *) address;
//    plasticity_weight_region_data =
//            spin1_malloc(sizeof(plasticity_weight_region_data_t) * n_synapse_types);
//    if (plasticity_weight_region_data == NULL) {
//    	io_printf(IO_BUF, "Could not initialise weight region data\n");
//        return NULL;
//    }
//    for (uint32_t s = 0; s < n_synapse_types; s++) {
//        plasticity_weight_region_data[s].min_weight = *plasticity_word++;
//        plasticity_weight_region_data[s].max_weight = *plasticity_word++;
//        plasticity_weight_region_data[s].reg_rate = kbits(*plasticity_word++);
//
////        plasticity_weight_region_data[s].a2_plus = *plasticity_word++;
////        plasticity_weight_region_data[s].a2_minus = *plasticity_word++;
//
//        io_printf(IO_BUF, "\tSynapse type %u: Min weight:%d, Max weight:%d, reg_rate: %k \n"
////        		"A2+:%d, A2-:%d"
//        		,
//                s, plasticity_weight_region_data[s].min_weight,
//                plasticity_weight_region_data[s].max_weight,
//				plasticity_weight_region_data[s].reg_rate
////                plasticity_weight_region_data[s].a2_plus,
////                plasticity_weight_region_data[s].a2_minus
//				);
//    }
//    io_printf(IO_BUF, "weight_initialise: completed successfully\n");
//
//    // Return end address of region
//    return (address_t) plasticity_word;
//}
