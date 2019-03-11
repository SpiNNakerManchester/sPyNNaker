#include <stdbool.h>
#include <stdint.h>

#ifndef __ROUTING_TABLE_H__

//! enum covering top level entries for routing tables in sdram
typedef enum routing_table_top_elements{
    N_TABLE_ENTRIES = 0, START_OF_SDRAM_ENTRIES = 1
} routing_table_top_elements;

//! \brief struct holding key and mask
typedef struct key_mask_t{
    // Key for the key_mask
    uint32_t key;

    // Mask for the key_mask
    uint32_t mask;
} key_mask_t;

//! \brief struct holding routing table entry data
typedef struct entry_t{
    // Key and mask
    key_mask_t key_mask;

    // Routing direction
    uint32_t route;

    // Source of packets arriving at this entry
    uint32_t source;
} entry_t;

//! \brief struct for holding table entries (NOT SURE HOW USFUL THIS IS NOW)
typedef struct table_t{

    // Number of entries in the table
    uint32_t size;

    // Entries in the table
    entry_t entries[];
} table_t;


//! \brief Get a mask of the Xs in a key_mask
//! \param[in] km: the key mask to get as xs
//! \return ???????????
static inline uint32_t key_mask_get_xs(key_mask_t km){
    return ~km.key & ~km.mask;
}


//! \brief Get a count of the Xs in a key_mask
//! \param[in] km: the key mask struct to count
//! \return ???????
static inline unsigned int key_mask_count_xs(key_mask_t km){
    return __builtin_popcount(key_mask_get_xs(km));
}


//! \brief Determine if two key_masks would match any of the same keys
//! \param[in] a: key mask struct a
//! \param[in] b: key masp struct b
//! \return bool that says if these key masks intersect
static inline bool key_mask_intersect(key_mask_t a, key_mask_t b){
    return (a.key & b.mask) == (b.key & a.mask);
}


//! \brief Generate a new key-mask which is a combination of two other key_masks
//! \brief c := a | b
//! \param[in] a: the key mask struct a
//! \param[in] b: the key mask struct b
//! \return a key mask struct when merged
static inline key_mask_t key_mask_merge(key_mask_t a, key_mask_t b){
    key_mask_t c;
    uint32_t new_xs = ~(a.key ^ b.key);
    c.mask = a.mask & b.mask & new_xs;
    c.key = (a.key | b.key) & c.mask;

    return c;
}

//! \brief gets a entry at a given position in the lists of tables in sdram
//! \param[in] routing_tables: the addresses list
//! \param[in] n_tables: how many in list
//! \param[in] entry_id_to_find: the entry your looking for
//! \param[out] entry_to_fill: the pointer to entry struct to fill in data
//! \return the pointer in sdram to the entry
entry_t* routing_table_sdram_stores_get_entry(
        table_t** routing_tables, uint32_t n_tables, uint32_t entry_id_to_find){

    uint32_t current_point_tracking = 0;
    for (uint32_t rt_index = 0; rt_index < n_tables; rt_index++){

        // get how many entries are in this block
        uint32_t entries_stored_here = routing_tables[rt_index]->size;

        // determine if the entry is in this table
        if (current_point_tracking + entries_stored_here > entry_id_to_find){
            uint32_t entry_index = entry_id_to_find - current_point_tracking;
            return &routing_tables[rt_index]->entries[entry_index];
        }
        else{
            current_point_tracking += entries_stored_here;
        }
    }

    log_error("should never get here. If so WTF!");
    rt_error(RTE_SWERR);
    return NULL;
}

//! \brief gets the length of the group of routing tables
//! \param[in] routing_tables: the addresses list
//! \param[in] n_tables: how many in list
//! \return the total number of entries over all the tables.
uint32_t routing_table_sdram_get_n_entries(
        table_t** routing_tables, uint32_t n_tables){
    uint32_t current_point_tracking = 0;
    for (uint32_t rt_index = 0; rt_index < n_tables; rt_index++){
        // get how many entries are in this block
        current_point_tracking += routing_tables[rt_index]->size;
    }
    return current_point_tracking;
}

//! \brief stores the routing tables entries into sdram at a specific sdram
//! address as one big router table
//! \param[in] routing_tables: the addresses list
//! \param[in] n_tables: how many in list
//! \param[in] sdram_address: the location in sdram to write data to
bool routing_table_sdram_store(
        table_t** routing_tables, uint32_t n_tables,
        address_t sdram_loc_for_compressed_entries){

    // cast to table struct
    table_t* table_format = (table_t*) sdram_loc_for_compressed_entries;

    // locate n entries overall and write to struct
    uint32_t n_entries = routing_table_sdram_get_n_entries(
        routing_tables, n_tables);
    log_info("compressed entries = %d", n_entries);
    table_format->size = n_entries;
    uint32_t main_entry_index = 0;

    // iterate though the entries writing to the struct as we go
    log_info("start copy over");
    for (uint32_t rt_index = 0; rt_index < n_tables; rt_index++){

        // get how many entries are in this block
        uint32_t entries_stored_here = routing_tables[rt_index]->size;
        log_info("copying over %d entries", entries_stored_here);
        if(entries_stored_here != 0){
            // take entry and plonk data in right sdram location
            log_info("doing sark copy");
            sark_mem_cpy(
                &table_format->entries[main_entry_index],
                routing_tables[rt_index]->entries,
                sizeof(entry_t));
            log_info("finished sark copy");
            main_entry_index += entries_stored_here;
            log_info("updated the main index to %d", main_entry_index);
        }
    }
    log_info("finished copy");
    return true;
}

//! \brief updates table stores accordingly.
//! \param[in] routing_tables: the addresses list
//! \param[in] n_tables: how many in list
//! \param[in] size_to_remove: the amount of size to remove from the table sets
void routing_table_remove_from_size(
        table_t** routing_tables, uint32_t n_tables,
        uint32_t size_to_remove){
    int rt_index = n_tables;
    while(size_to_remove != 0 || rt_index >= 0){
        if (routing_tables[rt_index]->size >= size_to_remove){
            uint32_t diff = routing_tables[rt_index]->size - size_to_remove;
            routing_tables[rt_index]->size = diff;
            size_to_remove = 0;
        }
        else{
            size_to_remove -= routing_tables[rt_index]->size;
            routing_tables[rt_index]->size = 0;
        }
        rt_index -= 1;
    }
    if (size_to_remove != 0){
        log_error("deleted more than what was available. WTF");
        rt_error(RTE_SWERR);
    }
}

//! \brief deduces sdram requirements for a given size of table
//! \param[in] n_entries: the number of entries expected to be in the table.
//! \return the number of bytes needed for this routing table
uint32_t routing_table_sdram_size_of_table(uint32_t n_entries){
    return sizeof(uint32_t) + (sizeof(entry_t) * n_entries);
}

#define __ROUTING_TABLE_H__
#endif  // __ROUTING_TABLE_H__
