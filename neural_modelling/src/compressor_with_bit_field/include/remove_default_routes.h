#include <stdbool.h>
#include "bit_set.h"
#include "routing_table.h"

#ifndef __REMOVE_DEFAULT_ROUTES_H__

static inline void remove_default_routes_minimise(table_t *table){
    // Mark the entries to be removed from the table
    bit_set_t remove;
    bool success = bit_set_init(&remove, table->size);
    if (!success){
        log_info("failed to initialise the bit_set. shutting down");
        spin1_exit(0);
    }

    // Work up the table from the bottom, marking entries to remove
    for (unsigned int i = table->size - 1; i < table->size; i--){
        // Get the current entry
        entry_t entry = table->entries[i];

        // See if it can be removed
        // only removed if Only one output direction which is a link. or
        // Only one input direction which is a link. or
        // Source is opposite to sink
        if (__builtin_popcount(entry.route) == 1 && (entry.route & 0x3f) &&
                __builtin_popcount(entry.source) == 1 &&
                (entry.source & 0x3f) &&
                (entry.route >> 3) == (entry.source & 0x7) &&
                (entry.source >> 3) == (entry.route & 0x7)){
            // The entry can be removed iff. it doesn't intersect with any entry
            // further down the table.
            bool remove_entry = true;
            for (unsigned int j = i + 1; j < table->size; j++){
                // If entry we're comparing with is already going to be
                // removed, ignore it.
                if (bit_set_contains(&remove, j)){
                    continue;
                }

                key_mask_t a = entry.key_mask;
                key_mask_t b = table->entries[j].key_mask;

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
    for (unsigned int insert = 0, read = 0; read < table->size; read++){
        // Grab the current entry before we potentially overwrite it
        entry_t current = table->entries[read];

        // Insert the entry if it isn't being removed
        if (!bit_set_contains(&remove, read)){
            table->entries[insert++] = current;
        }
    }

    // Update the table size
    table->size -= remove.count;

    // Clear up
    bit_set_delete(&remove);
}

#define __REMOVE_DEFAULT_ROUTES_H__
#endif  // __REMOVE_DEFAULT_ROUTES_H__
