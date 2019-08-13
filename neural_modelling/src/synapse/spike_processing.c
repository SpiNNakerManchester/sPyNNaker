/*
 * Copyright (c) 2017-2019 The University of Manchester
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

#include "spike_processing.h"
#include "population_table/population_table.h"
#include "synapse_row.h"
#include "synapses.h"
#include "synapse/structural_plasticity/synaptogenesis_dynamics.h"
#include "spin1_api_params.h"
#include <simulation.h>
#include <debug.h>

// The number of DMA Buffers to use
#define N_DMA_BUFFERS 2

// DMA tags
#define DMA_TAG_READ_SYNAPTIC_ROW 0
#define DMA_TAG_WRITE_PLASTIC_REGION 1

extern uint32_t time;
extern uint8_t end_of_timestep;

// True if the DMA "loop" is currently running
static bool dma_busy;
static uint32_t start;

// The DTCM buffers for the synapse rows
static dma_buffer dma_buffers[N_DMA_BUFFERS];

// The index of the next buffer to be filled by a DMA
static uint32_t next_buffer_to_fill;

// The index of the buffer currently being filled by a DMA read
static uint32_t buffer_being_read;

static uint32_t max_n_words;

static spike_t spike=-1;

static uint32_t single_fixed_synapse[4];

uint32_t number_of_rewires=0;
bool any_spike = false;

uint8_t kickstarts = 0;


//extern uint32_t measurement_in[1000];
//extern uint32_t measurement_out[1000];
//extern uint32_t measurement_index;

void start_dma_transfer(void *system_address, void *tcm_address,
    uint direction, uint length) {

    uint cpsr;

    cpsr = spin1_int_disable();

    start = time;

    uint desc = DMA_WIDTH << 24 | DMA_BURST_SIZE << 21 | direction << 19 | length;

    // Be careful, this transfer is done with no checks for maximum performances!
    // OK ONLY FOR STATIC NETWORK IN WHICH WE ARE SURE THAT WE HAVE NO MORE THAN 2 TRANSFERS AT A TIME
    dma[DMA_ADRS] = (uint) system_address;
    dma[DMA_ADRT] = (uint) tcm_address;
    dma[DMA_DESC] = desc;

    spin1_mode_restore(cpsr);
}


/* PRIVATE FUNCTIONS - static for inlining */

// Called when a DMA completes
static inline void _dma_complete() {


    // Get pointer to current buffer
    uint32_t current_buffer_index = buffer_being_read;
    dma_buffer *current_buffer = &dma_buffers[current_buffer_index];


    // Process synaptic row repeatedly
    bool subsequent_spikes = 0;
//    do {

//        // Are there any more incoming spikes from the same pre-synaptic
//        // neuron?population_table_get_next_address
//        subsequent_spikes = in_spikes_is_next_spike_equal(
//            current_buffer->originating_spike);

        // Process synaptic row, writing it back if it's the last time
        // it's going to be processed
        
        
//        if (!
        		synapses_process_synaptic_row(time, current_buffer->row,
            !subsequent_spikes, current_buffer_index);
//			) {
//            log_error(
//                "Error processing spike 0x%.8x for address 0x%.8x"
//                "(local=0x%.8x)",
//                current_buffer->originating_spike,
//                current_buffer->sdram_writeback_address,
//                current_buffer->row);
//
//            // Print out the row for debugging
//            for (uint32_t i = 0;
//                    i < (current_buffer->n_bytes_transferred >> 2); i++) {
//                log_error("%u: 0x%.8x", i, current_buffer->row[i]);
//            }
//
//            rt_error(RTE_SWERR);
//        }


//    } while (subsequent_spikes);

      // Start the next DMA transfer, so it is complete when we are finished
     // _setup_synaptic_dma_read(0, 0);

//        measurement_out[measurement_index] = tc[T1_COUNT];
//        measurement_index++;
}

static inline void _do_dma_read(
        address_t row_address, size_t n_bytes_to_transfer) {

    // Write the SDRAM address of the plastic region and the
    // Key of the originating spike to the beginning of DMA buffer
    dma_buffer *next_buffer = &dma_buffers[next_buffer_to_fill];
    next_buffer->sdram_writeback_address = row_address;
    next_buffer->originating_spike = spike;
    next_buffer->n_bytes_transferred = n_bytes_to_transfer;


    // Start a DMA transfer to fetch this synaptic row into current
    // buffer
    buffer_being_read = next_buffer_to_fill;
//    spin1_dma_transfer(
//        DMA_TAG_READ_SYNAPTIC_ROW, row_address, next_buffer->row, DMA_READ,
//        n_bytes_to_transfer);

    // Avoid DMA transfer if T2 cb has alredy completed
//    if(!end_of_timestep) {

        start_dma_transfer(
            row_address, next_buffer->row, DMA_READ, n_bytes_to_transfer);
        next_buffer_to_fill = (next_buffer_to_fill + 1) % N_DMA_BUFFERS;

        // Busy wait for DMA completion
        // Checks that T2 has not interrupted and that we are not in a new timestep
//        while((!end_of_timestep) && (start == time) && (!(dma[DMA_STAT] & 0x400)));
        while(!(dma[DMA_STAT] & 0x400));

//    }

}


static inline void _do_direct_row(address_t row_address) {
    single_fixed_synapse[3] = (uint32_t) row_address[0];
    synapses_process_synaptic_row(time, single_fixed_synapse, false, 0);
}

void _setup_synaptic_dma_read(uint arg1, uint arg2) {

    use(arg1);
    use(arg2);
    // ***********************************************************************
    kickstarts++;
    // ***********************************************************************

    // Set up to store the DMA location and size to read
    address_t row_address;
    size_t n_bytes_to_transfer;

    //bool setup_done = false;
    //bool finished = false;
    uint cpsr = 0;

//    cpsr = spin1_int_disable();

    //while (!finished) {

//        spin1_mode_restore(cpsr);
//        if (number_of_rewires) {
//            number_of_rewires--;
//            synaptogenesis_dynamics_rewire(time);
//            setup_done = true;
//        }

//        // If there's more rows to process from the previous spike
//        while (!setup_done && population_table_get_next_address(
//                &row_address, &n_bytes_to_transfer)) {
//
//            // This is a direct row to process
//            if (n_bytes_to_transfer == 0) {
//                _do_direct_row(row_address);
//            } else {
//                _do_dma_read(row_address, n_bytes_to_transfer);
//                setup_done = true;
//            }
//        }

        // If there's more incoming spikes
        cpsr = spin1_int_disable();

        while (in_spikes_get_next_spike(&spike)) {

            spin1_mode_restore(cpsr);

            log_debug("Checking for row for spike 0x%.8x\n", spike);


            // Decode spike to get address of destination synaptic row
            if (population_table_get_first_address(
                    spike, &row_address, &n_bytes_to_transfer)) {
                // This is a direct row to process
//                if (n_bytes_to_transfer == 0) {
//                    _do_direct_row(row_address);
//                } else {
            		cpsr = spin1_irq_disable();
                    if(!end_of_timestep) {
                    	_do_dma_read(row_address, n_bytes_to_transfer);
                    //setup_done = true;

                    // Protection against T2 event during the dma for this spike
//                    if(!end_of_timestep) {

                        dma[DMA_CTRL] = 0x08;
                        _dma_complete();
                    }
                    spin1_mode_restore(cpsr);
//                }
            }

            cpsr = spin1_int_disable();
        }
        // potentially restore here?

        //if (!setup_done) {
        //    finished = true; // finished trying for this spike
        //}
//        cpsr = spin1_int_disable(); // remove this too?
    //}

    // If the setup was not done, and there are no more spikes,
    // stop trying to set up synaptic DMAs
    //if (!setup_done) {
    //    log_debug("DMA not busy");
    dma_busy = false;
    //}
    spin1_mode_restore(cpsr);
}

static inline void _setup_synaptic_dma_write(uint32_t dma_buffer_index) {

    // Get pointer to current buffer
    dma_buffer *buffer = &dma_buffers[dma_buffer_index];

    // Get the number of plastic bytes and the write back address from the
    // synaptic row
    size_t n_plastic_region_bytes =
        synapse_row_plastic_size(buffer->row) * sizeof(uint32_t);

    log_debug("Writing back %u bytes of plastic region to %08x",
              n_plastic_region_bytes, buffer->sdram_writeback_address + 1);

    // Start transfer
    spin1_dma_transfer(
        DMA_TAG_WRITE_PLASTIC_REGION, buffer->sdram_writeback_address + 1,
        synapse_row_plastic_region(buffer->row),
        DMA_WRITE, n_plastic_region_bytes);
}


/* CALLBACK FUNCTIONS - cannot be static */

// Called when a multicast packet is received
void _multicast_packet_received_callback(uint key, uint payload) {
    use(payload);
    any_spike = true;
    log_debug("Received spike %x at %d, DMA Busy = %d", key, time, dma_busy);

//
////    measurement_in[measurement_index] = tc[T1_COUNT];
//
    	in_spikes_add_spike(key);

        // If we're not already processing synaptic DMAs,
        // flag pipeline as busy and trigger a feed event
        if (!dma_busy) {
        	// need this if to negate hazard of user event not being raised if
        	// one is already executing, and setup_dma_read had set dma_busy to false
        	if (spin1_schedule_callback(_setup_synaptic_dma_read, 0, 0, 1)) {
        		dma_busy = true;
        	}
        }





//
//        // **********
//        // If there was space to add spike to incoming spike queue
//        if (in_spikes_add_spike(key)) {
//
//            // If we're not already processing synaptic DMAs,
//            // flag pipeline as busy and trigger a feed event
//            if (!dma_busy) {
//
//                log_debug("Sending user event for new spike");
//                if (spin1_trigger_user_event(0, 0)) {
//                    dma_busy = true;
//                } else {
//                    log_error("Could not trigger user event\n");
//                }
//            }
//        } else {
//            log_debug("Could not add spike");
//        }
}


/* INTERFACE FUNCTIONS - cannot be static */

bool spike_processing_initialise(
        size_t row_max_n_words, uint mc_packet_callback_priority,
        uint incoming_spike_buffer_size) {

    // Allocate the DMA buffers
    for (uint32_t i = 0; i < N_DMA_BUFFERS; i++) {
        dma_buffers[i].row = (uint32_t*) spin1_malloc(
                row_max_n_words * sizeof(uint32_t));
        if (dma_buffers[i].row == NULL) {
            log_error("Could not initialise DMA buffers");
            return false;
        }
        log_debug(
            "DMA buffer %u allocated at 0x%08x", i, dma_buffers[i].row);
    }
    dma_busy = false;
    next_buffer_to_fill = 0;
    buffer_being_read = N_DMA_BUFFERS;
    max_n_words = row_max_n_words;

    // Allocate incoming spike buffer
    if (!in_spikes_initialize_spike_buffer(incoming_spike_buffer_size)) {
        return false;
    }

    // Set up for single fixed synapses (data that is consistent per direct row)run, SDP, DMA)) {
    single_fixed_synapse[0] = 0;
    single_fixed_synapse[1] = 1;
    single_fixed_synapse[2] = 0;

    // Set up the callbacks
    spin1_callback_on(MC_PACKET_RECEIVED,
            _multicast_packet_received_callback, mc_packet_callback_priority);

    return true;
}

void spike_processing_finish_write(uint32_t process_id) {
    _setup_synaptic_dma_write(process_id);
}

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overloaded
uint32_t spike_processing_get_buffer_overflows() {

    // Check for buffer overflow
    return in_spikes_get_n_buffer_overflows();
}

//! \brief get the address of the circular buffer used for buffering received
//! spikes before processing them
//! \return address of circular buffer
circular_buffer get_circular_buffer(){
    return buffer;
}

//! \brief set the DMA status
//! \param[in] busy: bool
//! \return None
void set_dma_busy(bool busy) {
    dma_busy = busy;
}

//! \brief retrieve the DMA status
//! \return bool
bool get_dma_busy() {
    return dma_busy;
}

//! \brief set the number of times spike_processing has to attempt rewiring
//! \return bool: currently, always true
bool do_rewiring(int number_of_rew) {
    number_of_rewires+=number_of_rew;
    return true;
}
//! \brief has this core received any spikes since the last batch of rewires?
//! \return bool
bool received_any_spike() {
    return any_spike;
}

uint32_t spike_processing_flush_in_buffer() {

    return in_spikes_flush_buffer();
}

void dma_int_disable() {

    vic[VIC_DISABLE] = (1 << DMA_DONE_INT);
}

void dma_int_enable() {

    vic[VIC_ENABLE] = (1 << DMA_DONE_INT);
}
