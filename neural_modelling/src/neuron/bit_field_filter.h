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

#include <bit_field.h>
#include <filter_info.h>
#include <debug.h>
#include "population_table/population_table.h"

bit_field_t *connectivity_bit_field;

//! the number of bit fields which were not able to be read in due to DTCM
//! limits
uint32_t failed_bit_field_reads = 0;

static bool bit_field_filter_initialise(address_t bitfield_region_address){

    filter_region_t* filter_region = (filter_region_t*) bitfield_region_address;
    uint32_t n_bit_fields = filter_region->n_filters;

    log_info("n bitfields = %d", n_bit_fields);

    // try allocating dtcm for starting array for bitfields
    connectivity_bit_field =
        spin1_malloc(sizeof(bit_field_t) * population_table_length());
    if (connectivity_bit_field == NULL){
        log_warning(
            "couldn't  initialise basic bit field holder. Will end up doing "
            "possibly more DMA's during the execution than required");
        return true;
    }

    // set all to NULL for when they not filled in.
    for (uint32_t cur_bit_field = 0; cur_bit_field < population_table_length();
            cur_bit_field++){
         connectivity_bit_field[cur_bit_field] = NULL;
    }

    // try allocating dtcm for each bit field
    for (uint32_t cur_bit_field = 0; cur_bit_field < n_bit_fields;
            cur_bit_field++){
        // get the key associated with this bitfield
        uint32_t key = filter_region->filters[cur_bit_field].key;
        uint32_t n_words = filter_region->filters[cur_bit_field].n_words;

        // locate the position in the array to match the master pop element.
        int position_in_array =
            population_table_position_in_the_master_pop_array(key);

        log_debug("putting key %d in position %d", key, position_in_array);

        // alloc sdram into right region
        connectivity_bit_field[position_in_array] = spin1_malloc(
            sizeof(bit_field_t) * n_words);
        if (connectivity_bit_field[position_in_array] == NULL){
            log_debug(
                "could not initialise bit field for key %d, packets with"
                " that key will use a DMA to check if the packet targets "
                "anything within this core. Potentially slowing down the "
                "execution of neurons on this core.", key);
            failed_bit_field_reads ++;
        } else{  // read in bit field into correct location

            // read in the bits for the bitfield (think this avoids a for loop)
            spin1_memcpy(
                connectivity_bit_field[position_in_array],
                filter_region->filters[cur_bit_field].data,
                sizeof(uint32_t) * n_words);

            // print out the bit field for debug purposes
            log_debug("bit field for key %d is :", key);
            for (uint32_t bit_field_word_index = 0;
                    bit_field_word_index < n_words;
                    bit_field_word_index++){
                log_debug(
                    "%x", connectivity_bit_field[position_in_array][
                        bit_field_word_index]);
            }
        }
    }
    population_table_set_connectivity_bit_field(connectivity_bit_field);
    return true;
}
