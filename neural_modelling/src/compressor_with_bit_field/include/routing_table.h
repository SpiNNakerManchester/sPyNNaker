#include <stdbool.h>
#include <stdint.h>

#ifndef __ROUTING_TABLE_H__

typedef struct _key_mask_t{
    // Key for the key_mask
    uint32_t key;

    // Mask for the key_mask
    uint32_t mask;
} key_mask_t;


// Get a mask of the Xs in a key_mask
static inline uint32_t key_mask_get_xs(key_mask_t km){
    return ~km.key & ~km.mask;
}


// Get a count of the Xs in a key_mask
static inline unsigned int key_mask_count_xs(key_mask_t km){
    return __builtin_popcount(key_mask_get_xs(km));
}


// Determine if two key_masks would match any of the same keys
static inline bool key_mask_intersect(key_mask_t a, key_mask_t b){
    return (a.key & b.mask) == (b.key & a.mask);
}


// Generate a new key-mask which is a combination of two other key_masks
//     c := a | b
static inline key_mask_t key_mask_merge(key_mask_t a, key_mask_t b){
    key_mask_t c;
    uint32_t new_xs = ~(a.key ^ b.key);
    c.mask = a.mask & b.mask & new_xs;
    c.key = (a.key | b.key) & c.mask;

    return c;
}


typedef struct _entry_t{
    // Key and mask
    key_mask_t key_mask;

    // Routing direction
    uint32_t route;

    // Source of packets arriving at this entry
    uint32_t source;
} entry_t;


typedef struct _table_t{

    // Number of entries in the table
    unsigned int size;

    // Entries in the table
    entry_t *entries;
} table_t;


#define __ROUTING_TABLE_H__
#endif  // __ROUTING_TABLE_H__
