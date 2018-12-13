#ifndef _DIRECT_SYNAPSES_H_
#define _DIRECT_SYNAPSES_H_

//! \brief setup for the direct synapses
//! \param[in] direct_matrix_address: the sdram base address for the direct
//                                    matrix
//! \param[out]: direct_synapses_address: the dtcm address for the direct matrix
//! \return: bool, that states true if successful, false otherwise.
bool direct_synapses_initialise(
    address_t direct_matrix_address, address_t *direct_synapses_address);

//! \brief returns the synapse for a given direct synaptic row.
// \param[in] row_address: the row address to read.
//! \return the synaptic row.
synaptic_row_t direct_synapses_get_direct_synapse(address_t row_address);

#endif // _DIRECT_SYNAPSES_H_