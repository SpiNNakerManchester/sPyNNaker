#ifndef _POPULATION_TABLE_H_
#define _POPULATION_TABLE_H_

#include "../common/neuron-typedefs.h"

//! \brief initiliser for master pop sturcutres. checks magic numbers and
//! that the strucutre is well formed.
//! \param[in] table_address the address in SDRAM where the master pop structure
//!            starts
//! \param[in] synapse_rows_address the address in SDRAM where synpase rows
//!            start
//! \param[in] row_max_n_words the max size a sybnapse row can be in words
//! \param[in] master_pop_magic_number the magic number identifer for the
//!            master pop data strcuture
//! \return true if the initialiser is valid false otherwise
bool population_table_initialise(
    address_t table_address, address_t synapse_rows_address,
    uint32_t *row_max_n_words, uint32_t master_pop_magic_number);

bool population_table_get_address(spike_t spike, address_t* row_address,
                                  size_t* n_bytes_to_transfer);

#endif // _POPULATION_TABLE_H_
