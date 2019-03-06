
//! \brief frees memory allocated and calls spin1 exit and sets the user0
//! error code correctly.
//! \param[in] header the header object
//! \param[in] table the data object holding the routing table entries
void cleanup_and_exit(header_t *header, table_t table) {
    // Free the memory used by the routing table.
    log_info("free sdram blocks which held router tables");
    FREE(table.entries);
    // Free the block of SDRAM used to load the routing table.
    sark_xfree(sv->sdram_heap, (void *) header, ALLOC_LOCK);

    log_info("completed router compressor");
    sark.vcpu->user2 = EXITED_CLEANLY;
    spin1_exit(0);
}

    // Prepare to minimise the routing tables
    log_info("looking for header using tag %u app_id %u", 1, sark_app_id());
    header_t *header = (header_t *) sark_tag_ptr(1, sark_app_id());
    log_info("reading data from 0x%08x", (uint32_t) header);
    print_header(header);

    // Load the routing table
    table_t table;
    log_info("start reading table");
    read_table(&table, header);
    log_info("finished reading table");

    // load in the bitfield addresses


    // Store intermediate sizes for later reporting (if we fail to minimise)
    uint32_t size_original, size_rde, size_oc;
    size_original = table.size;

    // Try to load the table
    log_info("check if compression is needed and compress if needed");
    if ((header->compress_only_when_needed == 1
            && !load_routing_table(&table, header->app_id))
            || header->compress_only_when_needed == 0) {

        // Otherwise remove default routes.
        log_info("remove default routes from minimiser");
        remove_default_routes_minimise(&table);
        size_rde = table.size;

        // Try to load the table
        log_info("check if compression is needed and try with no defaults");
        if ((header->compress_only_when_needed == 1
                && !load_routing_table(&table, header->app_id))
                || header->compress_only_when_needed == 0) {

            // Try to use Ordered Covering the minimise the table. This
            // requires that the table be reloaded from memory and that it
            // be sorted in ascending order of generality.

            log_info("free the tables entries");
            FREE(table.entries);
            read_table(&table, header);

            log_info("do qsort");
            qsort(table.entries, table.size, sizeof(entry_t), compare_rte);

            // Get the target length of the routing table
            log_info("acquire target length");
            uint32_t target_length = 0;
            if (header->compress_as_much_as_possible == 0) {
                target_length = rtr_alloc_max();
            }
            log_info("target length of %d", target_length);

            // Perform the minimisation
            aliases_t aliases = aliases_init();
            log_info("minimise");
            oc_minimise(&table, target_length, &aliases);
            log_info("done minimise");
            size_oc = table.size;

            // report size to the host for provenance aspects
            log_info("has compressed the router table to %d entries", size_oc);

            // Clean up the memory used by the aliases table
            log_info("clear up aliases");
            aliases_clear(&aliases);

            // Try to load the routing table
            log_info("try loading tables");
            if (!load_routing_table(&table, header->app_id)) {

                // Otherwise give up and exit with an error
                log_error(
                    "Failed to minimise routing table to fit %u entries. "
                    "(Original table: %u after removing default entries: %u "
                    "after Ordered Covering: %u).",
                    rtr_alloc_max(), size_original, size_rde, size_oc);

                // Free the block of SDRAM used to load the routing table.
                log_info("free sdram blocks which held router tables");
                FREE((void *) header);

                // set the failed flag and exit
                sark.vcpu->user2 = EXIT_FAIL;
                spin1_exit(0);
            } else {
                cleanup_and_exit(header, table);
            }
        }
    } else {
        cleanup_and_exit(header, table);
    }



        regions_position_in_sdram += 1;

    // cycle through each region pair, getting the bitfield one
    for(uint32_t region_id=0; region_id < n_pairs_of_addresses; region_id++){
        address_t bit_field_address =
            user_register_content[BIT_FIELD_AND_KEY_TO_ATOM_MAP][
                regions_position_in_sdram + BITFIELD_REGION];
        regions_position_in_sdram += ADDRESS_PAIR_LENGTH;

        // get total bitfields from bitfield region
        total_bit_fields += bit_field_address[0];
    }

    // allocate memory to store new struct
    sorted_bit_fields = MALLOC(total_bit_fields * sizeof(_bit_field_data_t));
    if (sorted_bit_fields == NULL){
         log_error(
            "failed to allocate enough dtcm for all bitfields, adjusting"
             "accordingly");
         uint max_available = platform_max_available_block_size();
         total_bit_fields = math.floor(
            max_available / sizeof(_bit_field_data_t));
         sorted_bit_fields = MALLOC(
            total_bit_fields * sizeof(_bit_field_data_t));
    }

    // read in for processing
    for




































// if the search ended on a failure, regenerate the best one
    log_info("check the last search vs the best search");
    if (last_search_point != best_search_point){
        log_info("regenerating best combination");
        binary_search();
        log_info("finished regenerating best combination");
    }

    // load router entries into router
    log_info("load the routing table entries into the router");
    load_routing_table_entries_to_router();
    log_info("finished loading the routing table");


    // remove merged bitfields from the cores bitfields
    log_info("start the removal of the bitfields from the chips cores "
             "bitfield regions.");
    remove_merged_bitfields_from_cores();
    log_info("finished the removal of the bitfields from the chips cores "
             "bitfields regions.");
    return true;