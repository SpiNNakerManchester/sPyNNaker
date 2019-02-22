#include "bit_set.h"
#include "routing_table.h"

#ifndef __MERGE_H__

typedef struct _merge_t{
    bit_set_t entries;  // Set of entries included in the merge
    table_t* table;    // Table against which the merge is defined

    key_mask_t key_mask; // key_mask resulting from the merge
    uint32_t route;    // Route taken by entries in the merge
    uint32_t source;   // Collective source of entries in the route
} merge_t;

#define FULL 0xffffffff
#define EMPTY 0x00000000
#define INIT_SOURCE 0x0
#define INIT_ROUTE 0x0


// Clear a merge
static inline void merge_clear(merge_t* m){
    // Clear the bit set
    bit_set_clear(&(m->entries));

    // Initialise the key_mask and route
    m->key_mask.key  = FULL;  // !!!...
    m->key_mask.mask = EMPTY;  // Matches nothing
    m->route = INIT_ROUTE;
    m->source = INIT_SOURCE;
}


// Initialise a merge
static inline bool merge_init(merge_t* m, table_t* table){
    // Store the table pointer, initialise the key_mask and route
    m->table = table;

    // Initialise the bit_set
    if (!bit_set_init(&(m->entries), table->size)){
        return false;
    }
    else{
        merge_clear(m);
        return true;
    }
}


// Destruct a merge
static inline void merge_delete(merge_t* m){
    // Free the bit set
    bit_set_delete(&m->entries);
}


// Add an entry to the merge
static inline void merge_add(merge_t* m, unsigned int i){
    // Add the entry to the bit set contained in the merge
    if (bit_set_add(&m->entries, i)){
        entry_t e = m->table->entries[i];

        // Get the key_mask
        if (m->key_mask.key == FULL && m->key_mask.mask == EMPTY){
            // If this is the first entry in the merge then the merge key_mask
            // is a copy of the entry key_mask.
            m->key_mask = e.key_mask;
        }
        else{
            // Otherwise update the key and mask associated with the merge
            m->key_mask = key_mask_merge(m->key_mask, e.key_mask);
        }

        // Add the route
        m->route |= e.route;
        m->source |= e.source;
    }
}

//! See if an entry is contained within a merge
static inline bool merge_contains(merge_t* m, unsigned int i){
  return bit_set_contains(&(m->entries), i);
}


// Remove an entry from the merge
static inline void merge_remove(merge_t* m, unsigned int i){
    // Remove the entry from the bit_set contained in the merge
    if (bit_set_remove(&(m->entries), i)){
        // Rebuild the key and mask from scratch
        m->route = INIT_ROUTE;
        m->source = INIT_SOURCE;
        m->key_mask.key  = FULL;
        m->key_mask.mask = EMPTY;
        for (unsigned int j = 0; j < m->table->size; j++){
            entry_t e = m->table->entries[j];

            if (bit_set_contains(&(m->entries), j)){
                m->route |= e.route;
                m->source |= e.source;
                if (m->key_mask.key  == FULL && m->key_mask.mask == EMPTY) {
                    // Initialise the key_mask
                    m->key_mask.key  = e.key_mask.key;
                    m->key_mask.mask = e.key_mask.mask;
                }
                else{
                    // Merge the key_mask
                    m->key_mask = key_mask_merge(m->key_mask, e.key_mask);
                }
            }
        }
    }
}


#define __MERGE_H__
#endif  // __MERGE_H__
