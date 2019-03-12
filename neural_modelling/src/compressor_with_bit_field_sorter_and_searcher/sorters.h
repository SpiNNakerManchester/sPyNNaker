#ifndef __SORTERS_H__

//! \brief sorter for redundant packet counts
//! \param[in/out] proc_cov_by_bit_field: the array of struct to be sorted
//! \param[in] length_of_internal_array: length of internal array
//! \param[in] worst_core_id: the core id to sort
void sort_by_redundant_packet_count(
        _proc_cov_by_bitfield_t** proc_cov_by_bit_field, 
        uint32_t length_of_internal_array, uint32_t worst_core_id){

    // sort by bubble sort so that the most redundant packet count
    // addresses are at the front
    bool moved = true;
    while (moved){
        moved = false;
        uint32_t element =
            proc_cov_by_bit_field[worst_core_id]->redundant_packets[0];
        for (uint index = 1; index < length_of_internal_array; index ++){
            uint32_t compare_element = proc_cov_by_bit_field[
                    worst_core_id]->redundant_packets[index];
                    
            if (element < compare_element){
                uint32_t temp_value = 0;

                // move to temp
                temp_value = element;

                // move compare over to element
                proc_cov_by_bit_field[worst_core_id]->redundant_packets[
                    index - 1] = compare_element;

                // move element over to compare location
                proc_cov_by_bit_field[worst_core_id]->redundant_packets[
                    index] = temp_value;

                // update flag
                moved = true;
            }
            else{  // jump to next element
                element = proc_cov_by_bit_field[
                    worst_core_id]->redundant_packets[index];
            }
        }
    }
}

//! \brief sort processor coverage by bitfield so that ones with longest length
//!  are at the front of the list
//! \param[in/out] proc_cov_by_bit_field: the array of structs to sort
//! \param[in] length_of_array: length of the array of structs
void sort_by_n_bit_fields(
        _proc_cov_by_bitfield_t** proc_cov_by_bit_field,
        uint32_t length_of_array){
    bool moved = true;
    while (moved){
        moved = false;
        _proc_cov_by_bitfield_t* element = proc_cov_by_bit_field[0];
        for (uint index = 1; index < length_of_array; index ++){
            _proc_cov_by_bitfield_t* compare_element =
                proc_cov_by_bit_field[index];
            if (element->length_of_list < compare_element->length_of_list){

                // create temp holder for moving objects
                _proc_cov_by_bitfield_t* temp_pointer;

                // move to temp
                temp_pointer = element;

                // move compare over to element
                proc_cov_by_bit_field[index - 1] = compare_element;

                // move element over to compare location
                proc_cov_by_bit_field[index] = temp_pointer;

                // update flag
                moved = true;
            }
            else{  // move to next element
                element = proc_cov_by_bit_field[index];
            }
        }
    }
}


// \brief sort bitfields by coverage by n_redundant_packets so biggest at front
//! \param[in/out] coverage: the array of structs to sort
//! \param[in] length_of_array: length of array of structs
void sort_bitfields_so_most_impact_at_front(
        coverage_t** coverage, uint32_t length_of_array){
    bool moved = true;
    while (moved){
        moved = false;
        coverage_t* element = coverage[0];
        for (uint index = 1; index < length_of_array; index ++){

            coverage_t* compare_element = coverage[index];

            if (element->n_redundant_packets <
                    compare_element->n_redundant_packets){

                coverage_t* temp_pointer;
                // move to temp
                temp_pointer = element;
                // move compare over to element
                coverage[index - 1] = compare_element;
                // move element over to compare location
                coverage[index] = temp_pointer;
                // update flag
                moved = true;
            }
            else{  // move to next element
                element = coverage[index];
            }
        }
    }
}

#define __SORTERS_H__
#endif  // __SORTERS_H__