/**
 *! \file
 *! \brief Common functions for kernel generation
 */
#include <common-typedefs.h>

/**
 *! \brief Function to do integer division without using divide
 */
uint16_t uidiv(uint16_t dividend, uint16_t divider, uint16_t *remainder);

/**
 *! \brief Get the post's coordinates in the pre's coordinate system
 */
void post_in_pre_world(uint16_t in_row, uint16_t in_col,
        uint16_t start_row, uint16_t start_col,
        uint16_t step_row, uint16_t step_col,
        uint16_t *out_row, uint16_t *out_col);

/**
 *! \brief Get the pre's coordinates in the post's coordinate system
 */
void pre_in_post_world(uint16_t in_row, uint16_t in_col, uint16_t start_row,
        uint16_t start_col, uint16_t step_row, uint16_t step_col,
        int16_t *out_row, int16_t *out_col);
