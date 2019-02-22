#include "aliases.h"
#include "bit_set.h"
#include "merge.h"
#include "routing_table.h"
#include <debug.h>

#ifndef __ORDERED_COVERING_H__

//! ?????????
typedef struct _sets_t{
    bit_set_t *best;
    bit_set_t *working;
} __sets_t;


// Get the goodness for a merge
static inline int merge_goodness(merge_t *m){
    return m->entries.count - 1;
}


// Get the index where the routing table entry resulting from a merge should be
// inserted.
static inline unsigned int oc_get_insertion_point(
        table_t *table, const unsigned int generality){
    // Perform a binary search of the table to find entries of generality - 1
    const unsigned int g_m_1 = generality - 1;
    unsigned int bottom = 0;
    unsigned int top = table->size;
    unsigned int pos = top / 2;

    while (bottom < pos && pos < top &&
            key_mask_count_xs(table->entries[pos].key_mask) != g_m_1){
        unsigned int entry_generality = key_mask_count_xs(
            table->entries[pos].key_mask);

        if (entry_generality < g_m_1){
            bottom = pos;
        }
        else{
            top = pos;
        }

        // Update the position
        pos = bottom + (top - bottom) / 2;
    }

    // Iterate through the table until either the next generality or the end of
    // the table is found.
    while (pos < table->size &&
            key_mask_count_xs(table->entries[pos].key_mask) < generality){
        pos++;
    }

    return pos;
}


// Remove from a merge any entries which would be covered by being existing
// entries if they were included in the given merge.
static inline bool oc_up_check(merge_t *m, int min_goodness){
    min_goodness = (min_goodness > 0) ? min_goodness : 0;

    // Track whether we remove any entries
    bool changed = false;

    // Get the point where the merge will be inserted into the table.
    unsigned int generality = key_mask_count_xs(m->key_mask);
    unsigned int insertion_index = oc_get_insertion_point(m->table, generality);

    // For every entry in the merge check that the entry would not be covered by
    // any existing entries if it were to be merged.
    for (unsigned int _i = m->table->size, i = m->table->size - 1;
            _i > 0 && merge_goodness(m) > min_goodness;
            _i--, i--){
        if (!merge_contains(m, i)){
          // If this entry is not contained within the merge skip it
          continue;
        }

        // Get the key_mask for this entry
        key_mask_t km = m->table->entries[i].key_mask;

        // Otherwise look through the table from the insertion point to the
        // current entry position to ensure that nothing covers the merge.
        for (unsigned int j = i + 1; j < insertion_index; j++){
            key_mask_t other_km = m->table->entries[j].key_mask;

            // If the key masks intersect then remove this entry from the merge
            // and recalculate the insertion index.
            if (key_mask_intersect(km, other_km)){
                changed = true;      // Indicate that the merge has changed
                merge_remove(m, i);  // Remove from the merge
                generality = key_mask_count_xs(m->key_mask);
                insertion_index = oc_get_insertion_point(m->table, generality);
            }
        }
    }

    // Completely empty the merge if its goodness drops below the minimum
    // specified
    if (merge_goodness(m) <= min_goodness){
        changed = true;
        merge_clear(m);
    }

    return changed;
}


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
static inline __sets_t _get_removables(
        merge_t *m, uint32_t settable, bool to_one, __sets_t sets){
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
        for (unsigned int i = 0; i < m->table->size; i++){
        
            // Skip if this isn't an entry
            if (!merge_contains(m, i)){
                continue;
            }
            
            // See if this entry should be removed
            key_mask_t km = m->table->entries[i].key_mask;
            
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


// Remove entries from a merge such that the merge would not cover existing
// entries positioned below the merge.
static inline void oc_down_check(merge_t *m, int min_goodness, aliases_t *a){
    min_goodness = (min_goodness > 0) ? min_goodness : 0;
    table_t *table = m->table;  // Retrieve the table

    while (merge_goodness(m) > min_goodness){
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
            table, key_mask_count_xs(m->key_mask));

        for (unsigned int i = insertion_point;
                i < table->size && stringency > 0;
                i++){

            key_mask_t km = table->entries[i].key_mask;
            if (key_mask_intersect(km, m->key_mask)){
                if (!aliases_contains(a, km)) {
                    // The entry doesn't contain any aliases so we need to
                    // avoid hitting the key that has just been identified.
                    covered_entries = true;
                    _get_settable(
                        m->key_mask, km, &stringency, &set_to_zero,
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

                            if (key_mask_intersect(km, m->key_mask)){
                                covered_entries = true;
                                _get_settable(m->key_mask, km, &stringency,
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
            return;
        }

        if (stringency == 0){
            // We can't avoid a covered entry at all so we need to empty the
            // merge entirely.
            merge_clear(m);
            return;
        }

        // Determine which entries could be removed from the merge and then pick
        // the smallest number of entries to remove.
        __sets_t sets = {MALLOC(sizeof(bit_set_t)), MALLOC(sizeof(bit_set_t))};
        bit_set_init(sets.best, m->entries.count);
        bit_set_init(sets.working, m->entries.count);

        sets = _get_removables(m, set_to_zero, false, sets);
        sets = _get_removables(m, set_to_one, true, sets);

        // Remove the specified entries
        unsigned int entry = 0;
        for (unsigned int i = 0; i < m->table->size; i++){
            if (merge_contains(m, i)){
                if (bit_set_contains(sets.best, entry)){
                    // Remove this entry from the merge
                    merge_remove(m, i);
                }
                entry++;
            }
        }

        // Tidy up
        bit_set_delete(sets.best);
        FREE(sets.best);
        sets.best=NULL;
        bit_set_delete(sets.working);
        FREE(sets.working);
        sets.working=NULL;

        // If the merge only contains 1 entry empty it entirely
        if (m->entries.count == 1){
            merge_clear(m);
        }
    }
}


// Get the best merge which can be applied to a routing table
static inline merge_t oc_get_best_merge(table_t* table, aliases_t *aliases){
    // Keep track of which entries have been considered as part of merges.
    bit_set_t considered;
    bool success = bit_set_init(&considered, table->size);
    if (!success){
        log_info("failed to initialise the bit_set. shutting down");
        spin1_exit(0);
    }

    // Keep track of the current best merge and also provide a working merge
    merge_t best, working;
    merge_init(&best, table);
    merge_init(&working, table);

    // For every entry in the table see with which other entries it could be
    // merged.
    for (unsigned int i = 0; i < table->size; i++){

        // If this entry has already been considered then skip to the next
        if (bit_set_contains(&considered, i)){
            continue;
        }

        // Otherwise try to build a merge
        // Clear the working merge
        merge_clear(&working);

        // Add to the merge
        merge_add(&working, i);

        // Mark this entry as considered
        bit_set_add(&considered, i);

        // Get the entry
        entry_t entry = table->entries[i];

        // Try to merge with other entries
        for (unsigned int j = i+1; j < table->size; j++){

            // Get the other entry
            entry_t other = table->entries[j];
            if (entry.route == other.route){

                // If the routes are the same then the entries may be merged
                // Add to the merge
                merge_add(&working, j);

                // Mark the other entry as considered
                bit_set_add(&considered, j);
            }
        }

        if (merge_goodness(&working) <= merge_goodness(&best)){
            continue;
        }

        // Perform the first down check
        oc_down_check(&working, merge_goodness(&best), aliases);

        if (merge_goodness(&working) <= merge_goodness(&best)){
            continue;
        }

        // Perform the up check, seeing if this actually makes a change to the
        // size of the merge.
        if (oc_up_check(&working, merge_goodness(&best))){
            if (merge_goodness(&working) <= merge_goodness(&best)){
                continue;
            }

            // If the up check did make a change then the down check needs to
            // be run again.
            oc_down_check(&working, merge_goodness(&best), aliases);
        }

        // If the merge is still better than the current best merge we swap the
        // current and best merges to record the new best merge.
        if (merge_goodness(&best) < merge_goodness(&working)){
            merge_t other = working;
            working = best;
            best = other;
        }
    }

    // Tidy up
    merge_delete(&working);
    bit_set_delete(&considered);

    // Return the best merge
    return best;
}


// Apply a merge to the table against which it is defined
static inline void oc_merge_apply(merge_t *m, aliases_t *aliases){
    // Get the new entry
    entry_t new_entry;
    new_entry.key_mask = m->key_mask;
    new_entry.route = m->route;
    new_entry.source = m->source;

    // Get the insertion point for the new entry
    unsigned int insertion_point = oc_get_insertion_point(
    m->table, key_mask_count_xs(m->key_mask));

    // Keep track of the size of the finished table
    table_t *table = m->table;
    unsigned int new_size = table->size + 1;

    // Create a new aliases list with sufficient space for the key_masks of all
    // of the entries in the merge.
    alias_list_t *new_aliases = alias_list_new(m->entries.count);
    aliases_insert(aliases, new_entry.key_mask, new_aliases);

    // Use two iterators to move through the table copying entries from one
    // position to the other as required.
    unsigned int insert = 0;
    for (unsigned int remove = 0; remove < table->size; remove++){
        // Grab the current entry before we possibly overwrite it
        entry_t current = table->entries[remove];

        // Insert the new entry if this is the correct position at which to do
        // so
        if (remove == insertion_point){
            table->entries[insert] = new_entry;
            insert++;
        }

        if (!merge_contains(m, remove)){
            // If this entry is not contained within the merge then copy it
            // from its current position to its new position.
            table->entries[insert] = current;
            insert++;
        }
        else{
            // Otherwise update the aliases table to account for the entry
            // which is being merged.
            key_mask_t km = table->entries[remove].key_mask;
            uint32_t source = table->entries[remove].source;

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
            new_size--;
        }
    }

    // If inserting beyond the old end of the table then perform the insertion
    // at the new end of the table.
    if (insertion_point == table->size){
        table->entries[insert] = new_entry;
    }

    // Record the new size of the table
    table->size = new_size;
}


// Apply the ordered covering algorithm to a routing table
// Minimise the table until either the table is shorter than the target length
// or no more merges are possible.
static inline void oc_minimise(
        table_t *table, unsigned int target_length, aliases_t *aliases){
    while (table->size > target_length){
        // Get the best possible merge, if this merge is empty then break out
        // of the loop.
        merge_t merge = oc_get_best_merge(table, aliases);
        unsigned int count = merge.entries.count;

        if (count > 1){
            // Apply the merge to the table if it would result in merging
            // actually occurring.
            oc_merge_apply(&merge, aliases);
        }

        // Free any memory used by the merge
        merge_delete(&merge);

        // Break out of the loop if no merge could be performed (indicating
        // that no more minimisation is possible).
        if (count < 2){
            break;
        }
    }
}


#define __ORDERED_COVERING_H__
#endif  // __ORDERED_COVERING_H__
