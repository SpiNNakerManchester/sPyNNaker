#include "aliases.h"
#include "bit_set.h"
#include "merge.h"
#include "../common/compressor_common/routing_table.h"
#include "remove_default_routes.h"
#include "../common/compressor_common/platform.h"
#include <debug.h>

#ifndef __ORDERED_COVERING_H__

//! \brief ?????????
typedef struct _sets_t{
    bit_set_t *best;
    bit_set_t *working;
} __sets_t;


//! \brief Get the goodness for a merge
//! /param[in] merge: the merge
//! \return the goodness of the merge.
static inline int merge_goodness(merge_t *merge){
    return merge->entries.count - 1;
}


//! \brief Get the index where the routing table entry resulting from a merge
//! should be inserted.
//! \param[in/out]  routing_tables: the routing tables in sdram
//! \param[in] n_tables: the number of routing tables in sdram
//! \param[in] generality: ??????????
static inline unsigned int oc_get_insertion_point(
        table_t** routing_tables, uint32_t n_tables,
        const unsigned int generality){
    // Perform a binary search of the table to find entries of generality - 1
    const unsigned int g_m_1 = generality - 1;
    unsigned int bottom = 0;
    unsigned int top = routing_table_sdram_get_n_entries(
        routing_tables, n_tables);
    unsigned int pos = top / 2;

    // get first entry
    entry_t* entry = routing_table_sdram_stores_get_entry(
        routing_tables, n_tables, pos);
    unsigned int count_xs = key_mask_count_xs(entry->key_mask);

    // iterate till found something
    while (bottom < pos && pos < top && count_xs != g_m_1){

        if (count_xs < g_m_1){
            bottom = pos;
        }
        else{
            top = pos;
        }

        // Update the position
        pos = bottom + (top - bottom) / 2;

        // update entry and count
        entry = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, pos);
        count_xs = key_mask_count_xs(entry->key_mask);
    }

    // Iterate through the table until either the next generality or the end of
    // the table is found.

    while (pos < routing_table_sdram_get_n_entries(
            routing_tables, n_tables) && count_xs < generality){
        pos++;
        entry = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, pos);
        count_xs = key_mask_count_xs(entry->key_mask);
    }

    return pos;
}


//! \brief Remove from a merge any entries which would be covered by being
//! existing entries if they were included in the given merge.
//! \param[in] merge: the merge to consider
//! \param[in] min_goodness: ????????
//! \param[in/out]  routing_tables: the routing tables in sdram
//! \param[in] n_tables: the number of routing tables in sdram
//! \return bool flag saying if the table was changed or not
static inline bool oc_up_check(
        merge_t *merge, int min_goodness, table_t** routing_tables,
        uint32_t n_tables){
    min_goodness = (min_goodness > 0) ? min_goodness : 0;

    // Track whether we remove any entries
    bool changed = false;

    // Get the point where the merge will be inserted into the table.
    unsigned int generality = key_mask_count_xs(merge->key_mask);
    unsigned int insertion_index = oc_get_insertion_point(
        routing_tables, n_tables, generality);

    // For every entry in the merge check that the entry would not be covered by
    // any existing entries if it were to be merged.
    for (unsigned int _i = routing_table_sdram_get_n_entries(
                routing_tables, n_tables),
            i = routing_table_sdram_get_n_entries(
                routing_tables, n_tables) - 1;
            _i > 0 && merge_goodness(merge) > min_goodness;
            _i--, i--){
        if (!merge_contains(merge, i)){
          // If this entry is not contained within the merge skip it
          continue;
        }

        // Get the key_mask for this entry
        key_mask_t km = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, i)->key_mask;

        // Otherwise look through the table from the insertion point to the
        // current entry position to ensure that nothing covers the merge.
        for (unsigned int j = i + 1; j < insertion_index; j++){
            key_mask_t other_km = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, j)->key_mask;

            // If the key masks intersect then remove this entry from the merge
            // and recalculate the insertion index.
            if (key_mask_intersect(km, other_km)){

                // Indicate the the merge has changed
                changed = true;

                // Remove from the merge
                merge_remove(merge, i, routing_tables, n_tables);
                generality = key_mask_count_xs(merge->key_mask);
                insertion_index = oc_get_insertion_point(
                    routing_tables, n_tables, generality);
            }
        }
    }

    // Completely empty the merge if its goodness drops below the minimum
    // specified
    if (merge_goodness(merge) <= min_goodness){
        changed = true;
        merge_clear(merge);
    }

    return changed;
}

//! \brief ????????????????
//! \param[in] merge_km: ???????
//! \param[in] covered_km: ????????
//! \param[in] stringency: ????????
//! \param[in] set_to_zero: ???????
//! \param[in] set_to_one: ????????
static inline void _get_settable(
        key_mask_t merge_km, key_mask_t covered_km, unsigned int *stringency,
        uint32_t *set_to_zero, uint32_t *set_to_one){

    // We can "set" any bit where the merge contains an X and the covered
    // entry doesn't.
    uint32_t settable =
        ~key_mask_get_xs(covered_km) & key_mask_get_xs(merge_km);
    unsigned int new_stringency = __builtin_popcount(settable);

    uint32_t this_set_to_zero = settable &  covered_km.key;
    uint32_t this_set_to_one  = settable & ~covered_km.key;

    // The stringency indicates how many bits *could* be set to avoid the cover.
    // If this new stringency is lower than the existing stringency then we
    // reset which bits may be set.
    if (new_stringency < *stringency){
        // Update the stringency count
        *stringency  = new_stringency;
        *set_to_zero = this_set_to_zero;
        *set_to_one  = this_set_to_one;
    }
    else if (new_stringency == *stringency){
        *set_to_zero |= this_set_to_zero;
        *set_to_one  |= this_set_to_one;
    }
}

//! \brief ???????????
//! \param[in] m: Merge from which entries will be removed
//! \param[in] settable: Mask of bits to set
//! \param[in] to_one:  True if setting to one, otherwise false
//! \param[in] sets: bitfields of some form
//! \param[in] routing_tables: the list of routing tables in sdram
//! \param[in] n_tables: the number of tables
static inline __sets_t _get_removables(
        merge_t *m, uint32_t settable, bool to_one, __sets_t sets,
        table_t** routing_tables, uint32_t n_tables){
    // For each bit which we are trying to set while the best set doesn't
    // contain only one entry.
    for (uint32_t bit = (1 << 31); bit > 0 && sets.best->count != 1;
            bit >>= 1){

        // If this bit cannot be set we ignore it
        if (!(bit & settable)){
          continue;
        }
        
        // Loop through the table adding to the working set any entries with
        // either a X or a 0 or 1 (as specified by `to_one`) to the working set
        // of entries to remove.
        unsigned int entry = 0;
        for (unsigned int i = 0; i <
                routing_table_sdram_get_n_entries(routing_tables, n_tables);
                i++){
        
            // Skip if this isn't an entry
            if (!merge_contains(m, i)){
                continue;
            }
            
            // See if this entry should be removed
            key_mask_t km = routing_table_sdram_stores_get_entry(
                routing_tables, n_tables, i)->key_mask;
            
            // check entry has x or 1 or 0 in this position.
            if (bit & ~km.mask || (!to_one && bit & km.key) ||
                    (to_one && bit & ~km.key)){
                    
                // NOTE: Indexing by position in merge!
                bit_set_add(sets.working, entry);
            }
            
            // Increment the index into the merge set
            entry++;
        }
        
        // If `working` contains fewer entries than `best` or `best` is empty
        // swap `working and best`. Otherwise just empty the working set.
        if (sets.best->count == 0 || sets.working->count < sets.best->count){
            // Perform the swap
            bit_set_t *c = sets.best;
            sets.best = sets.working;
            sets.working = c;
        }
        
        // Clear the working merge
        bit_set_clear(sets.working);
    }
    
    return sets;
}


//! \brief Remove entries from a merge such that the merge would not cover
//! existing entries positioned below the merge.
//! \param[in] merge: the merge to eventually apply
//! \param[in] min_goodness: ????????
//! \param[in] a: ????????
//! \param[out] failed_to_malloc: bool flag saying if it failed due to malloc
//! \param[in] routing_tables: the list of routing tables in sdram
//! \param[in] n_tables: the number of tables
//! \return bool that says if it was successful or not
static inline bool oc_down_check(
        merge_t *merge, int min_goodness, aliases_t *a, bool* failed_to_malloc,
        table_t** routing_tables, uint32_t n_tables){
    min_goodness = (min_goodness > 0) ? min_goodness : 0;

    while (merge_goodness(merge) > min_goodness){
        // Record if there were any covered entries
        bool covered_entries = false;

        // Not at all stringent
        unsigned int stringency = 33;

        // Mask of which bits could be set to zero
        uint32_t set_to_zero = 0x0;

        // Mask of which bits could be set to one
        uint32_t set_to_one  = 0x0;

        // Look at every entry between the insertion index and the end of the
        // table to see if there are any entries which could be covered by the
        // entry resulting from the merge.
        unsigned int insertion_point = oc_get_insertion_point(
            routing_tables, n_tables, key_mask_count_xs(merge->key_mask));

        for (unsigned int i = insertion_point;
                i < routing_table_sdram_get_n_entries(
                    routing_tables, n_tables) && stringency > 0;
                i++){

            key_mask_t km = routing_table_sdram_stores_get_entry(
                routing_tables, n_tables, i)->key_mask;
            if (key_mask_intersect(km, merge->key_mask)){
                if (!aliases_contains(a, km)) {
                    // The entry doesn't contain any aliases so we need to
                    // avoid hitting the key that has just been identified.
                    covered_entries = true;
                    _get_settable(
                        merge->key_mask, km, &stringency, &set_to_zero,
                        &set_to_one);
                }
                else{
                    // We need to avoid any key_masks contained within the
                    // alias table.
                    alias_list_t *the_alias_list = aliases_find(a, km);
                    while (the_alias_list != NULL){
                        for (unsigned int j = 0;
                                j < the_alias_list->n_elements; j++){
                            km = alias_list_get(the_alias_list, j).key_mask;

                            if (key_mask_intersect(km, merge->key_mask)){
                                covered_entries = true;
                                _get_settable(merge->key_mask, km, &stringency,
                                              &set_to_zero, &set_to_one);
                            }
                        }

                        // Progress through the alias list
                        the_alias_list = the_alias_list->next;
                    }
                }
            }
        }

        if (!covered_entries){
            // If there were no covered entries then we needn't do anything
            return true;
        }

        if (stringency == 0){
            // We can't avoid a covered entry at all so we need to empty the
            // merge entirely.
            merge_clear(merge);
            return true;
        }

        // Determine which entries could be removed from the merge and then
        //pick the smallest number of entries to remove.
        __sets_t sets;

        // allocate and free accordingly
        sets.best = MALLOC(sizeof(bit_set_t));


        if (sets.best == NULL){
            log_error("failed to alloc sets best");
            *failed_to_malloc = true;
            return false;
        }

        sets.working = MALLOC(sizeof(bit_set_t));
        if(sets.working == NULL){
            log_error("failed to alloc sets working");
            *failed_to_malloc = true;

            // free stuff already malloc
            FREE(&sets.best);
            return false;
        }

        bool success = bit_set_init(sets.best, merge->entries.count);
        if (!success){
            log_error("failed to init the bitfield best");
            *failed_to_malloc = true;

            // free stuff already malloc
            FREE(&sets.best);
            FREE(&sets.working);
            return false;
        }
        bit_set_init(sets.working, merge->entries.count);
        if (!success){
            log_error("failed to init the bitfield working.");
            *failed_to_malloc = true;

            // free stuff already malloc
            FREE(&sets.best);
            FREE(&sets.working);
            return false;
        }

        sets = _get_removables(
            merge, set_to_zero, false, sets, routing_tables, n_tables);
        sets = _get_removables(
            merge, set_to_one, true, sets, routing_tables, n_tables);

        // Remove the specified entries
        unsigned int entry = 0;
        for (unsigned int i = 0; i <routing_table_sdram_get_n_entries(
                routing_tables, n_tables); i++){
            if (merge_contains(merge, i)){
                if (bit_set_contains(sets.best, entry)){
                    // Remove this entry from the merge
                    merge_remove(merge, i, routing_tables, n_tables);
                }
                entry++;
            }
        }

        // Tidy up
        bit_set_delete(sets.best);
        FREE(&sets.best);
        sets.best=NULL;
        bit_set_delete(sets.working);
        FREE(&sets.working);
        sets.working=NULL;

        // If the merge only contains 1 entry empty it entirely
        if (merge->entries.count == 1){
            merge_clear(merge);
        }
    }
    return true;
}


//! \brief Get the best merge which can be applied to a routing table
//! \param[in] routing_tables: the list of routing tables in sdram
//! \param[in] n_tables: the number of tables
//! \param[in] aliases: ???????????
//! \param[in] best: the best merge to find
//! \param[out] failed_by_malloc: bool flag saying failed by malloc
//! \return bool saying if successful or not.
static inline bool oc_get_best_merge(
        table_t** routing_tables, uint32_t n_tables, aliases_t * aliases,
        merge_t * best, bool* failed_by_malloc){

    // Keep track of which entries have been considered as part of merges.
    bit_set_t considered;
    bool success = bit_set_init(
        &considered,
        routing_table_sdram_get_n_entries(routing_tables, n_tables));

    if (!success){
        log_info("failed to initialise the bit_set. throwing response malloc");
        *failed_by_malloc = true;
        return false;
    }

    // Keep track of the current best merge and also provide a working merge
    merge_t working;
    success = merge_init(
        best, routing_table_sdram_get_n_entries(routing_tables, n_tables));
    if (!success){
        log_info("failed to init the merge best. throw response malloc");
        *failed_by_malloc = true;

        // free bits we already done
        FREE(&considered);

        // return false
        return false;
    }

    success = merge_init(
        &working,
        routing_table_sdram_get_n_entries(routing_tables, n_tables));
     if (!success){
        log_info("failed to init the merge working. throw response malloc");
        *failed_by_malloc = true;

        // free bits we already done
        FREE(&best);
        FREE(&considered);

        // return false
        return false;
    }

    // For every entry in the table see with which other entries it could be
    // merged.
    for (unsigned int i = 0;
            i < routing_table_sdram_get_n_entries(routing_tables, n_tables);
            i++){

        // If this entry has already been considered then skip to the next
        if (bit_set_contains(&considered, i)){
            continue;
        }

        // Otherwise try to build a merge
        // Clear the working merge
        merge_clear(&working);

        // Add to the merge
        merge_add(&working, i, routing_tables, n_tables);

        // Mark this entry as considered
        bit_set_add(&considered, i);

        // Get the entry
        entry_t* entry = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, i);

        // Try to merge with other entries
        for (unsigned int j = i+1;
                j < routing_table_sdram_get_n_entries(
                    routing_tables, n_tables);
                j++){

            // Get the other entry
            entry_t* other = routing_table_sdram_stores_get_entry(
                routing_tables, n_tables, j);

            // check if mergable
            if (entry->route == other->route){

                // If the routes are the same then the entries may be merged
                // Add to the merge
                merge_add(&working, j, routing_tables, n_tables);

                // Mark the other entry as considered
                bit_set_add(&considered, j);
            }
        }

        if (merge_goodness(&working) <= merge_goodness(best)){
            continue;
        }

        // Perform the first down check
        success = oc_down_check(
            &working, merge_goodness(best), aliases, failed_by_malloc,
            routing_tables, n_tables);
        if (!success){
            log_error("failed to down check. ");

            // free bits we already done
            FREE(&best);
            FREE(&considered);

            return false;
        }

        if (merge_goodness(&working) <= merge_goodness(best)){
            continue;
        }

        // Perform the up check, seeing if this actually makes a change to the
        // size of the merge.
        if (oc_up_check(
                &working, merge_goodness(best), routing_tables, n_tables)){
            if (merge_goodness(&working) <= merge_goodness(best)){
                continue;
            }

            // If the up check did make a change then the down check needs to
            // be run again.
            success = oc_down_check(
                &working, merge_goodness(best), aliases, failed_by_malloc,
                routing_tables, n_tables);
            if (!success){
                log_error("failed to down check. ");

                // free bits we already done
                FREE(&best);
                FREE(&considered);

                return false;
            }

        }

        // If the merge is still better than the current best merge we swap the
        // current and best merges to record the new best merge.
        if (merge_goodness(best) < merge_goodness(&working)){
            merge_t other = working;
            working = *best;
            *best = other;
        }
    }

    // Tidy up
    merge_delete(&working);
    bit_set_delete(&considered);

    // found the best merge. return true
    return true;
}


//! \brief Apply a merge to the table against which it is defined
//! \param[in] merge: the merge to apply to the routing tables
//! \param[in] aliases: ??????????????
//! \param[in] routing_tables: the list of routing tables in sdram
//! \param[in] n_tables: the number of tables
static inline void oc_merge_apply(
        merge_t *merge, aliases_t *aliases, table_t** routing_tables,
        uint32_t n_tables){
    // Get the new entry
    entry_t new_entry;
    new_entry.key_mask = merge->key_mask;
    new_entry.route = merge->route;
    new_entry.source = merge->source;

    // Get the insertion point for the new entry
    unsigned int insertion_point = oc_get_insertion_point(
        routing_tables, n_tables, key_mask_count_xs(merge->key_mask));

    // Keep track of the amount of reduction of the finished table
    unsigned int reduced_size = 0;

    // Create a new aliases list with sufficient space for the key_masks of all
    // of the entries in the merge.
    alias_list_t *new_aliases = alias_list_new(merge->entries.count);
    aliases_insert(aliases, new_entry.key_mask, new_aliases);

    // Use two iterators to move through the table copying entries from one
    // position to the other as required.
    uint32_t insert = 0;
    for (uint32_t remove = 0;
            remove < routing_table_sdram_get_n_entries(
                routing_tables, n_tables); remove++){

        // Grab the current entry before we possibly overwrite it
        entry_t* current = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, remove);

        // Insert the new entry if this is the correct position at which to do
        // so
        if (remove == insertion_point){
            entry_t* insert_entry = routing_table_sdram_stores_get_entry(
                routing_tables, n_tables, insert);

            // move data between entries
            insert_entry->key_mask.key = new_entry.key_mask.key;
            insert_entry->key_mask.mask = new_entry.key_mask.mask;
            insert_entry->route = new_entry.route;
            insert_entry->source = new_entry.source;
            insert++;
        }

        if (!merge_contains(merge, remove)){
            // If this entry is not contained within the merge then copy it
            // from its current position to its new position.
            entry_t* insert_entry = routing_table_sdram_stores_get_entry(
                routing_tables, n_tables, insert);
            insert_entry->key_mask.key = current->key_mask.key;
            insert_entry->key_mask.mask = current->key_mask.mask;
            insert_entry->route = current->route;
            insert_entry->source = current->source;
            insert++;
        }
        else{
            // Otherwise update the aliases table to account for the entry
            // which is being merged.
            key_mask_t km = routing_table_sdram_stores_get_entry(
                routing_tables, n_tables, remove)->key_mask;

            uint32_t source = routing_table_sdram_stores_get_entry(
                routing_tables, n_tables, remove)->source;

            if (aliases_contains(aliases, km)){
                // Join the old list of aliases with the new
                alias_list_join(new_aliases, aliases_find(aliases, km));

                // Remove the old aliases entry
                aliases_remove(aliases, km);
            }
            else{
                // Include the key_mask in the new list of aliases
                alias_list_append(new_aliases, km, source);
            }

            // Decrement the final table size to account for this entry being
            // removed.
            reduced_size++;
        }
    }

    // If inserting beyond the old end of the table then perform the insertion
    // at the new end of the table.
    if (insertion_point == routing_table_sdram_get_n_entries(
            routing_tables, n_tables)){
        entry_t* insert_entry = routing_table_sdram_stores_get_entry(
            routing_tables, n_tables, insert);
        insert_entry->key_mask.key = new_entry.key_mask.key;
        insert_entry->key_mask.mask = new_entry.key_mask.mask;
        insert_entry->route = new_entry.route;
        insert_entry->source = new_entry.source;
    }

    // Record the new size of the table
    routing_table_remove_from_size(routing_tables, n_tables, reduced_size);
}


// Apply the ordered covering algorithm to a routing table
// Minimise the table until either the table is shorter than the target length
// or no more merges are possible.
//! \param[in/out] routing_tables: the list of routing tables in sdram
//! \param[in] n_tables: the number of tables
//! \param[in] target_length: the length to compress to
//! \param[in] aliases: whatever
//! \param[out] failed_by_malloc: bool flag stating that it failed due to malloc
//! \param[out] finished_by_control: bool flag saying it failed to control force
//! \param[out] timer_for_compression_attempt: bool flag saying it ran out of
//!                                           time
//! \param[out] finish_compression_flag: bool flag saying once compressed, still
//!          could not compress enough to meet target length.
//! \param[in] compress_only_when_needed: only compress when needed
//! \param[in] compress_as_much_as_possible: only compress to normal routing
//!       table length
//! \return bool saying if it was successful or not.
static inline bool oc_minimise(
        table_t** routing_tables, uint32_t n_tables, uint32_t target_length,
        aliases_t* aliases, bool *failed_by_malloc, bool *finished_by_control,
        bool *timer_for_compression_attempt, bool *finish_compression_flag,
        bool compress_only_when_needed, bool compress_as_much_as_possible){

    // check if any compression actually needed
    log_info("check if need to compress");
    log_info("target length is %d", target_length);
    log_info("compress only when needed is %d", compress_only_when_needed);
    log_info("n entries is %d",
             routing_table_sdram_get_n_entries(routing_tables, n_tables));
    if (compress_only_when_needed &&
            (routing_table_sdram_get_n_entries(routing_tables, n_tables)
             < target_length)){
        log_info("does not need compression.");
        return true;
    }

    // remove default routes and check lengths again
    log_info("try removing default routes");
    bool success = remove_default_routes_minimise(routing_tables, n_tables);
    if (!success){
        log_error("failed to remove default routes due to malloc. failing");
        *failed_by_malloc = true;
        return false;
    }

    log_info(
        "check if without default routes, if that makes compression needed");
    if (compress_only_when_needed &&
            (routing_table_sdram_get_n_entries(routing_tables, n_tables)
             < target_length)){
        log_info("does not need compression.");
        return true;
    }

    // by setting target length to 0, it'll not finish till no other merges
    // are available.
    if (compress_as_much_as_possible){
        target_length = 0;
    }

    // start the timer tick interrupt count down
    log_info("set off timer tracker");
    spin1_resume(SYNC_NOWAIT);

    // start the merger process
    log_info("start compression true attempt");
    while ((routing_table_sdram_get_n_entries(
            routing_tables, n_tables) > target_length) &&
            !timer_for_compression_attempt && !finished_by_control){
        
        if (*finish_compression_flag){
            log_error("failed due to timing limitations");
            *timer_for_compression_attempt = true;
            spin1_pause();
            return false;
        }

        // Get the best possible merge, if this merge is empty then break out
        // of the loop.
        merge_t merge;
        bool success = oc_get_best_merge(
            routing_tables, n_tables, aliases, &merge, failed_by_malloc);
        if (!success){
            log_error("failed to do get best merge.");
            return false;
        }

        unsigned int count = merge.entries.count;

        if (count > 1){
            // Apply the merge to the table if it would result in merging
            // actually occurring.
            oc_merge_apply(&merge, aliases, routing_tables, n_tables);
        }

        // Free any memory used by the merge
        merge_delete(&merge);

        // Break out of the loop if no merge could be performed (indicating
        // that no more minimisation is possible).
        if (count < 2){
            break;
        }
    }
    log_info("compressed!!!");
    return true;
}


#define __ORDERED_COVERING_H__
#endif  // __ORDERED_COVERING_H__
