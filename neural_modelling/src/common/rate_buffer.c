/*
 * Copyright (c) 2013-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/* circular_buffer.c
 *
 *  SUMMARY
 *    The essential feature of the buffer used in this implementation is that it
 *    requires no critical-section interlocking --- PROVIDED THERE ARE ONLY TWO
 *    PROCESSES: a producer/consumer pair. If this is changed, then a more
 *    intricate implementation will probably be required, involving the use
 *    of enable/disable interrupts.
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *
 *  CREATION DATE
 *    10 December, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 10 December 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 */

#include "rate_buffer.h"
#include "utils.h"

#include "spin-print.h"

rate_buffer rate_buffer_initialize(
	uint32_t size)
{
    uint32_t real_size = size;
    if (!is_power_of_2(real_size)) {
	    real_size = next_power_of_2(size);
    }

    rate_buffer buffer = sark_alloc(1, sizeof(_rate_buffer));
    buffer->buffer = sark_alloc(real_size, sizeof(rate_t));

    if (buffer == NULL || buffer->buffer == NULL) {
	    return NULL;
    }

    buffer->buffer_size = real_size - 1;
    buffer->input = 0;
    buffer->output = 0;
    buffer->overflows = 0;
    return buffer;
}

void rate_buffer_print_buffer(
	rate_buffer buffer)
{
    uint32_t i = buffer->output;

    io_printf(IO_BUF, "[");
    while (i != buffer->input) {
	    io_printf(IO_BUF, "%u %f", buffer->buffer[i].key, buffer->buffer[i].rate);
	    i = (i + 1) & buffer->buffer_size;
	    if (i != buffer->input) {
	        io_printf(IO_BUF, ", ");
	    }
    }
    io_printf(IO_BUF, "]\n");
}
