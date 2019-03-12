#ifndef __BIT_FIELD_READER_H__


//! \brief reads in bitfields, makes a few maps, sorts into most priority.
//! \return bool that states if it succeeded or not.
bool read_in_bit_fields(){

    // count how many bitfields there are in total
    uint position_in_region_data = 0;
    n_bf_addresses = 0;
    uint32_t n_pairs_of_addresses =
        user_register_content[REGION_ADDRESSES][N_PAIRS];
    position_in_region_data = START_OF_ADDRESSES_DATA;
    log_info("n pairs of addresses = %d", n_pairs_of_addresses);

    // malloc the bt fields by processor
    bit_field_by_processor = MALLOC(
        n_pairs_of_addresses * sizeof(_bit_field_by_processor_t));
    if (bit_field_by_processor == NULL){
        log_error("failed to allocate memory for pairs, if it fails here. "
                  "might as well give up");
        return false;
    }

    // build processor coverage by bitfield
    _proc_cov_by_bitfield_t** proc_cov_by_bf = MALLOC(
        n_pairs_of_addresses * sizeof(_proc_cov_by_bitfield_t*));
    if (proc_cov_by_bf == NULL){
        log_error("failed to allocate memory for processor coverage by "
                  "bitfield, if it fails here. might as well give up");
        return false;
    }
    log_info("finished malloc proc_cov_by_bf");

    // iterate through a processors bitfield region and get n bitfields
    for (uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){

        // malloc for n redundant packets
        proc_cov_by_bf[r_id] = MALLOC(sizeof(
            _proc_cov_by_bitfield_t));
        if (proc_cov_by_bf[r_id] == NULL){
            log_error("failed to allocate memory for processor coverage for "
                      "region %d. might as well give up", r_id);
            return false;
        }

        // track processor id
        bit_field_by_processor[r_id].processor_id =
            user_register_content[REGION_ADDRESSES][
                position_in_region_data + PROCESSOR_ID];
        proc_cov_by_bf[r_id]->processor_id =
            user_register_content[REGION_ADDRESSES][
                position_in_region_data + PROCESSOR_ID];
        log_info("bit_field_by_processor in region %d processor id = %d",
                 r_id, bit_field_by_processor[r_id].processor_id);

        // locate data for malloc memory calcs
        address_t bit_field_address = (address_t) user_register_content[
            REGION_ADDRESSES][position_in_region_data + BITFIELD_REGION];
        log_info("bit_field_region = %x", bit_field_address);
        position_in_region_data += ADDRESS_PAIR_LENGTH;

        log_info("safety check. bit_field key is %d",
                 bit_field_address[BIT_FIELD_BASE_KEY]);
        uint32_t pos_in_bitfield_region = N_BIT_FIELDS;
        uint32_t core_n_bit_fields = bit_field_address[pos_in_bitfield_region];
        log_info("there are %d core bit fields", core_n_bit_fields);
        pos_in_bitfield_region = START_OF_BIT_FIELD_TOP_DATA;
        n_bf_addresses += core_n_bit_fields;

        // track lengths
        proc_cov_by_bf[r_id]->length_of_list = core_n_bit_fields;
        bit_field_by_processor[r_id].length_of_list = core_n_bit_fields;
        log_info("bit field by processor with region %d, has length of %d",
                 r_id, core_n_bit_fields);

        // malloc for bitfield region addresses
        bit_field_by_processor[r_id].bit_field_addresses = MALLOC(
            core_n_bit_fields * sizeof(address_t));
        if (bit_field_by_processor[r_id].bit_field_addresses == NULL){
            log_error("failed to allocate memory for bitfield addresses for "
                      "region %d, might as well fail", r_id);
            return false;
        }

        // malloc for n redundant packets
        proc_cov_by_bf[r_id]->redundant_packets = MALLOC(
            core_n_bit_fields * sizeof(uint));
        if (proc_cov_by_bf[r_id]->redundant_packets == NULL){
            log_error("failed to allocate memory for processor coverage for "
                      "region %d, might as well fail", r_id);
            return false;
        }

        // populate tables: 1 for addresses where each bitfield component starts
        //                  2 n redundant packets
        for (uint32_t bit_field_id = 0; bit_field_id < core_n_bit_fields;
                bit_field_id++){
            bit_field_by_processor[r_id].bit_field_addresses[
                bit_field_id] =
                    (address_t) &bit_field_address[pos_in_bitfield_region];
            log_info("bitfield at region %d at index %d is at address %x",
                r_id, bit_field_id,
                bit_field_by_processor[r_id].bit_field_addresses[
                    bit_field_id]);

            uint32_t n_redundant_packets =
                detect_redundant_packet_count(
                    (address_t) &bit_field_address[pos_in_bitfield_region]);
            proc_cov_by_bf[r_id]->redundant_packets[bit_field_id] =
                n_redundant_packets;
            log_info("prov cov by bitfield for region %d, redundant packets "
                     "at index %d, has n redundant packets of %d",
                     r_id, bit_field_id, n_redundant_packets);

            pos_in_bitfield_region +=
                START_OF_BIT_FIELD_DATA + bit_field_address[
                    pos_in_bitfield_region + BIT_FIELD_N_WORDS];
        }
    }

    // sort out teh searcher bitfields. as now first time where can do so
    // NOTE: by doing it here, the response from the uncompressed can be
    // handled correctly.
    log_info("setting up search bitfields");
    bool success = set_up_search_bitfields();
    if (!success){
        log_error("can not allocate memory for search fields.");
        return false;
    }
    log_info("finish setting up search bitfields");

    // set off a none bitfield compression attempt, to pipe line work
    log_info("sets off the uncompressed version of the search");
    set_off_no_bit_field_compression();

    // populate the bitfield by coverage
    log_info("n bitfield addresses = %d", n_bf_addresses);
    sorted_bit_fields = MALLOC(n_bf_addresses * sizeof(address_t));
    if(sorted_bit_fields == NULL){
        log_error("cannot allocate memory for the sorted bitfield addresses");
        return false;
    }

    sorted_bit_fields_processor_ids =
        MALLOC(n_bf_addresses * sizeof(uint32_t));
    if (sorted_bit_fields_processor_ids == NULL){
        log_error("cannot allocate memory for the sorted bitfields with "
                  "processors ids");
        return false;
    }

    uint length_n_redundant_packets = 0;
    uint * redundant_packets = MALLOC(n_bf_addresses * sizeof(uint));

    // filter out duplicates in the n redundant packets
    position_in_region_data = START_OF_ADDRESSES_DATA;
    for (uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
        // cycle through the bitfield registers again to get n bitfields per
        // core
        address_t bit_field_address =
            (address_t) user_register_content[REGION_ADDRESSES][
                position_in_region_data + BITFIELD_REGION];
        position_in_region_data += ADDRESS_PAIR_LENGTH;
        uint32_t core_n_bit_fields = bit_field_address[N_BIT_FIELDS];

        // check that each bitfield redundant packets are unqiue and add to set
        for (uint32_t bit_field_id = 0; bit_field_id < core_n_bit_fields;
                bit_field_id++){
            uint x_packets = proc_cov_by_bf[
                r_id]->redundant_packets[bit_field_id];
            // check if seen this before
            bool found = false;
            for (uint index = 0; index < length_n_redundant_packets; index++){
                if(redundant_packets[index] == x_packets){
                    found = true;
                }
            }
            // if not a duplicate, add to list and update size
            if (!found){
                redundant_packets[length_n_redundant_packets] = x_packets;
                length_n_redundant_packets += 1;
            }
        }
    }
    log_info("length of n redundant packets = %d",
             length_n_redundant_packets);

    // malloc space for the bitfield by coverage map
    coverage_t** coverage = MALLOC(
        length_n_redundant_packets * sizeof(coverage_t*));
    if (coverage == NULL){
        log_error("failed to malloc memory for the bitfields by coverage. "
                  "might as well fail");
        return false;
    }

    // go through the unique x redundant packets and build the list of
    // bitfields for it
    for (uint32_t r_packet_index = 0;
            r_packet_index < length_n_redundant_packets; r_packet_index++){
        // malloc a redundant packet entry
        log_debug("try to allocate memory of size %d for coverage at index %d",
                  sizeof(coverage_t), r_packet_index);
        coverage[r_packet_index] = MALLOC(sizeof(coverage_t));
        if (coverage[r_packet_index] == NULL){
            log_error("failed to malloc memory for the bitfields by coverage "
                      "for index %d. might as well fail", r_packet_index);
            return false;
        }

        // update the redundant packet pointer
        coverage[r_packet_index]->n_redundant_packets =
            redundant_packets[r_packet_index];

        // search to see how long the list is going to be.
        uint32_t n_bf_with_same_r_packets = 0;
        for (uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
            uint length = proc_cov_by_bf[r_id]->length_of_list;
            for(uint red_packet_index = 0; red_packet_index < length;
                    red_packet_index ++){
                if(proc_cov_by_bf[r_id]->redundant_packets[
                        red_packet_index] == redundant_packets[r_packet_index]){
                    n_bf_with_same_r_packets += 1;
                }
            }
        }

        // update length of list
        coverage[r_packet_index]->length_of_list = n_bf_with_same_r_packets;

        // malloc list size for these addresses of bitfields with same
        // redundant packet counts.
        coverage[r_packet_index]->bit_field_addresses = MALLOC(
            n_bf_with_same_r_packets * sizeof(address_t));
        if(coverage[r_packet_index]->bit_field_addresses == NULL){
            log_error("failed to allocate memory for the coverage on index %d"
                      " for addresses. might as well fail.", r_packet_index);
            return false;
        }

        // malloc list size for the corresponding processors ids for the
        // bitfields
        log_debug(
            "trying to allocate %d bytes, for x bitfields same xr packets %d",
            n_bf_with_same_r_packets * sizeof(uint32_t),
            n_bf_with_same_r_packets);
        coverage[r_packet_index]->processor_ids = MALLOC(
            n_bf_with_same_r_packets * sizeof(uint32_t));
        if(coverage[r_packet_index]->processor_ids == NULL){
            log_error("failed to allocate memory for the coverage on index %d"
                      " for processors. might as well fail.", r_packet_index);
            return false;
        }

        // populate list of bitfields addresses which have same redundant
        //packet count.
        log_debug(
            "populating list of bitfield addresses with same packet count");
        uint32_t processor_id_index = 0;
        for (uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
            log_info("prov cov for region id %d has length %d", r_id,
                     proc_cov_by_bf[r_id]->length_of_list);
            for(uint red_packet_index = 0;
                    red_packet_index < proc_cov_by_bf[r_id]->length_of_list;
                    red_packet_index ++){

                log_info(
                    "bit field redundant packets at index %d ,%d is %d and "
                    "looking for %d ",
                    r_id, r_packet_index,
                    proc_cov_by_bf[r_id]->redundant_packets[red_packet_index],
                    redundant_packets[r_packet_index]);
                if(proc_cov_by_bf[r_id]->redundant_packets[red_packet_index] ==
                        redundant_packets[r_packet_index]){
                    log_info(
                        "found! at %x",
                        bit_field_by_processor[ r_id].bit_field_addresses[
                            red_packet_index]);

                    coverage[r_packet_index]->bit_field_addresses[
                        processor_id_index] = bit_field_by_processor[
                            r_id].bit_field_addresses[red_packet_index];

                    coverage[r_packet_index]->processor_ids[processor_id_index]
                        = bit_field_by_processor[r_id].processor_id;

                    processor_id_index += 1;
                }
            }
        }
        log_info(
            "processor id index = %d and need to fill in %d elements",
            processor_id_index, n_bf_with_same_r_packets);
    }

    // free the redundant packet tracker, as now tailored ones are in the dict
    FREE(redundant_packets);

    // order the bitfields based off the impact to cores redundant packet
    // processing
    order_bit_fields_based_on_impact(
        coverage, proc_cov_by_bf, n_pairs_of_addresses,
        length_n_redundant_packets);

    // free the data holders we don't care about now that we've got our
    // sorted bitfields list
    for(uint r_id = 0; r_id < n_pairs_of_addresses; r_id++){
        coverage_t* cov_element = coverage[r_id];
        FREE(cov_element->bit_field_addresses);
        FREE(cov_element->processor_ids);
        FREE(cov_element);
        _proc_cov_by_bitfield_t* proc_cov_element =
            proc_cov_by_bf[r_id];
        FREE(proc_cov_element->redundant_packets);
        FREE(proc_cov_element);
    }
    FREE(coverage);
    FREE(proc_cov_by_bf);

    for(uint32_t bf_index = 0; bf_index < n_bf_addresses; bf_index++){
        log_info(
            "bitfield address for sorted in index %d is %x",
            bf_index, sorted_bit_fields[bf_index]);
    }

    return true;
}



#define __BIT_FIELD_READER_H__
#endif  // __BIT_FIELD_READER_H__