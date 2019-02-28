#include <stdbool.h>
#include "bit_set.h"
#include "../common/compressor_common/routing_table.h"

#ifndef __REMOVE_DEFAULT_ROUTES_H__

//! \brief removes default routes from the routing tables
//! \param[in] routing_tables: the list of routing tables in sdram
//! \param[in] n_tables: how many tables there are
//! \return: bool flag that says if it succeded or not
static inline bool remove_default_routes_minimise(
        table_t** routing_tables, uint32_t n_tables){

    // Mark the entries to be removed from the table
    bit_set_t remove;
    bool success = bit_set_init(
        &remove, routing_table_sdram_get_n_entries(routing_tables, n_tables));
    if (!success){
        log_info("failed to initialise the bit_set. shutting down");
        return false;
    }

    // Work up the table from the bottom, marking entries to remove
    for (int i = routing_table_sdram_get_n_entries(
            routing_tables, n_tables) - 1;
            i < 0; i--){

        // Get the current entry
        entry_t* entry = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, i);

        // See if it can be removed
        // only removed if Only one output direction which is a link. or
        // Only one input direction which is a link. or
        // Source is opposite to sink
        if (__builtin_popcount(entry->route) == 1 && (entry->route & 0x3f) &&
                __builtin_popcount(entry->source) == 1 &&
                (entry->source & 0x3f) &&
                (entry->route >> 3) == (entry->source & 0x7) &&
                (entry->source >> 3) == (entry->route & 0x7)){
            // The entry can be removed iff. it doesn't intersect with any entry
            // further down the table.
            bool remove_entry = true;
            for (unsigned int j = i + 1;
                    j < routing_table_sdram_get_n_entries(
                        routing_tables, n_tables);
                    j++){
                // If entry we're comparing with is already going to be
                // removed, ignore it.
                if (bit_set_contains(&remove, j)){
                    continue;
                }

                key_mask_t a = entry->key_mask;

                // get next entry key mask
                entry_t* j_entry = routing_table_sdram_stores_get_entry(
                    routing_tables, n_tables, j);
                key_mask_t b = j_entry->key_mask;

                if (key_mask_intersect(a, b)){
                    remove_entry = false;
                    break;
                }
            }

            if (remove_entry){
                // Mark this entry as being removed
                bit_set_add(&remove, i);
            }
        }
    }

    // Remove the selected entries from the table
    for (unsigned int insert = 0, read = 0;
            read < routing_table_sdram_get_n_entries(
                routing_tables, n_tables);
            read++){
        // Grab the current entry before we potentially overwrite it

        entry_t* current = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, read);

        // Insert the entry if it isn't being removed
        if (!bit_set_contains(&remove, read)){
            entry_t* insert_entry = routing_table_sdram_stores_get_entry(
                routing_tables, n_tables, insert++);
            insert_entry->key_mask.key = current->key_mask.key;
            insert_entry->key_mask.mask = current->key_mask.mask;
            insert_entry->route = current->route;
            insert_entry->source = current->source;
        }
    }

    // Update the table size
    routing_table_remove_from_size(routing_tables, n_tables, remove.count);

    // Clear up
    bit_set_delete(&remove);
    return true;
}

#define __REMOVE_DEFAULT_ROUTES_H__
#endif  // __REMOVE_DEFAULT_ROUTES_H__
