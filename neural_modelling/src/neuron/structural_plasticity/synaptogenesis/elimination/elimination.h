#ifndef _ELIMINATION_H_
#define _ELIMINATION_H_

#include <neuron/structural_plasticity/sp_structs.h>

address_t synaptogenesis_elimination_init(address_t data);

//! \brief Elimination rule for synaptogenesis
//! \param[in] rewiring_data Pointer to rewiring data
//! \param[in] current_state Pointer to current state
//! \param[in] time Time of elimination
//! \param[in] row The row to eliminate from
//! \return if row was modified
static inline bool synaptogenesis_elimination_rule(rewiring_data_t *rewiring_data,
        current_state_t *current_state, uint32_t time, address_t row);

#endif // _ELIMINATION_H_
