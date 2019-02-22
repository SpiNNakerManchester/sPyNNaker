#include <spin1_api.h>
#include <debug.h>
#include <bit_field.h>
#include <sdp_no_scp.h>
#include "common-typedefs.h"
#include "../common/compressor_common/platform.h"
#include "../common/compressor_common/routing_table.h"
#include "../common/compressor_common/compression_sdp_formats.h"
/*****************************************************************************/
/* SpiNNaker routing table minimisation with bitfield integration.
 *
 * Minimise a routing table loaded into SDRAM and load the minimised table into
 * the router using the specified application ID.
 *
 * the exit code is stored in the user1 register
 *
 * The memory address with tag "1" is expected contain the following struct
 * (entry_t is defined in `routing_table.h` but is described below).
*/

typedef enum interrupt_priority{
    TIMER_TICK_PRIORITY = -1, SDP_PRIORITY = 1, COMPRESSION_START_PRIORITY = 2
} interrupt_priority;

//! word to byte multiplier
#define WORD_TO_BYTE_MULTIPLIER 4

//! timeout for sdp message attempt
#define _SDP_TIMEOUT 100

//! random port as 0 is in use by scamp/sark
#define RANDOM_PORT 4

//! \brief the timer control logic.
bool timer_for_compression_attempt = false;

//! \brief the sdram location to write the compressed router table into
address_t sdram_loc_for_compressed_entries;

//! \brief number of times a compression time slot has occurred
bool finish_compression_flag = false;

//! \brief bool flag to say if i was forced to stop by the compressor control
bool finished_by_compressor_force = false;

//! \brief store for addresses for routing entries in sdram
address_t * routing_entries_addresses;

//! control flag for running compression only when needed
uint32_t compress_only_when_needed = 0;

//! control flag for compressing as much as possible
uint32_t compress_as_much_as_possible = 0;

//! how many packets waiting for
uint32_t number_of_packets_waiting_for = 0;

//! the number of addresses currently stored
uint32_t routing_addresses_stored = 0;

//! \brief the control core id for sending responses to
uint32_t control_core_id = 0;

//! \brief sdp message to send acks to the control core with
sdp_msg_pure_data my_msg;

//! bool flag pointer to allow minimise to report if it failed due to malloc
//! issues
bool failed_by_malloc = false;

//! \brief sends a sdp message back to the
void send_sdp_message_response(){
    my_msg.dest_port = control_core_id;
    // send sdp packet
    while (!spin1_send_sdp_msg((sdp_msg_t *) &my_msg, _SDP_TIMEOUT)) {
        // Empty body
    }
}

void return_malloc_response_message(){
    // set message ack finished state to malloc fail
    my_msg.data[FINISHED_STATE] = FAILED_MALLOC;

    // send message
    send_sdp_message_response();
}

void return_success_response_message(){
    // set message ack finished state to malloc fail
    my_msg.data[FINISHED_STATE] = SUCCESSFUL_COMPRESSION;

    // send message
    send_sdp_message_response();
}

void return_failed_by_force_response_message(){
       // set message ack finished state to malloc fail
    my_msg.data[FINISHED_STATE] = FORCED_BY_COMPRESSOR_CONTROL;

    // send message
    send_sdp_message_response();
}

void return_failed_by_time_response_message(){
       // set message ack finished state to malloc fail
    my_msg.data[FINISHED_STATE] = RAN_OUT_OF_TIME;

    // send message
    send_sdp_message_response();
}

void return_failed_by_space_response_message(){
       // set message ack finished state to malloc fail
    my_msg.data[FINISHED_STATE] = FAILED_TO_COMPRESS;

    // send message
    send_sdp_message_response();
}

void start_compression_process(){
    failed_by_malloc = false;
    bool success = oc_minimise(table_t *table, unsigned int target_length, aliases_t *aliases)
    if (success){
        return_success_response_message();
    }
    else{
        if (failed_by_malloc){  // malloc failed somewhere
            return_malloc_response_message();
        }
        else if (finished_by_compressor_force){  // control killed it
            return_failed_by_force_response_message();
        }
        else if (timer_for_compression_attempt){  // ran out of time
            return_failed_by_time_response_message();
        }
        else{  // after finishing compression, still could not fit into table.
            return_failed_by_space_response_message();
        }
    }
}

//! \brief the sdp control entrance. 
void _sdp_handler(uint mailbox, uint port) {
    use(port);

    log_info("received packet");
    // get data from the sdp message
    sdp_msg_pure_data *msg = (sdp_msg_pure_data *) mailbox;

    // record control core.
    control_core_id = msg->srce_port;
    log_info("control core is %d", control_core_id);

    log_info("command code is %d", msg->data[COMMAND_CODE]);

    // get command code
    if (msg->data[COMMAND_CODE] == START_OF_COMPRESSION_DATA_STREAM){

        // location where to store the compressed (size
        sdram_loc_for_compressed_entries =
            (address_t)  msg->data[ADDRESS_FOR_COMPRESSED];

        // set up fake heap
        log_info("setting up fake heap for sdram usage");
        platform_new_heap_creation((address_t) msg->data[FAKE_HEAP_DATA]);
        log_info("finished setting up fake heap for sdram usage");

        // set up packet tracker
        number_of_packets_waiting_for =
            msg->data[N_SDP_PACKETS_TILL_DELIVERED];
        number_of_packets_waiting_for -= 1;

        // set up addresses data holder
        routing_entries_addresses = MALLOC(
            msg->data[TOTAL_N_ADDRESSES] * sizeof(address_t));
        if (routing_entries_addresses == NULL){
            log_error(
                "failed to allocate memory for holding the addresses "
                "locations");
            sark_msg_free((sdp_msg_t*) msg);
            return_malloc_response_message();
        }
        else{

            // store this set into the store
            log_info("store routing table addresses into store");
            sark_mem_cpy(
                &my_msg.data[START_OF_ADDRESSES],
                &routing_entries_addresses[routing_addresses_stored],
                my_msg.data[N_ADDRESSES_IN_PACKET] * WORD_TO_BYTE_MULTIPLIER);

            // keep tracker updated
            routing_addresses_stored += msg->data[N_ADDRESSES_IN_PACKET];
            log_info("finished storing routing table address into store");

            // if no more packets to locate, then start compression process
            if (number_of_packets_waiting_for == 0){
                spin1_schedule_callback(
                    start_compression_process, 0, 0,
                    COMPRESSION_START_PRIORITY);
            }

            // free message
            sark_msg_free((sdp_msg_t*) msg);
        }

    }
    else if(msg->data[COMMAND_CODE] == EXTRA_DATA_FOR_COMPRESSION_DATA_STREAM){
        if (routing_entries_addresses == NULL){
            log_error(
                "ignoring extra routing table addresses packet, as cant store"
                " them");
        }
        else{

            // store this set into the store
            log_info("store extra routing table addresses into store");
            number_of_packets_waiting_for -= 1;
            sark_mem_cpy(
                &my_msg.data[START_OF_ADDRESSES_EXTENSION],
                &routing_entries_addresses[routing_addresses_stored],
                my_msg.data[EXTRA_STREAM_N_ADDRESSES] *
                WORD_TO_BYTE_MULTIPLIER);

            // keep tracker updated
            routing_addresses_stored += msg->data[EXTRA_STREAM_N_ADDRESSES];
            log_info("finished storing extra routing table address into store");

            // if no more packets to locate, then start compression process
            if (number_of_packets_waiting_for == 0){
                spin1_schedule_callback(
                    start_compression_process, 0, 0,
                    COMPRESSION_START_PRIORITY);
            }
        }

        // free message
        sark_msg_free((sdp_msg_t*) msg);
    }
    else if(msg->data[COMMAND_CODE] == COMPRESSION_RESPONSE){
        log_error("I really should not be receiving this!!! WTF");
        sark_msg_free((sdp_msg_t*) msg);
    }
    else if (msg->data[COMMAND_CODE] == STOP_COMPRESSION_ATTEMPT){
        finished_by_compressor_force = true;
        sark_msg_free((sdp_msg_t*) msg);
    }
}

//! \brief timer interrupt for controlling time taken to try to compress table
//! \param[in] unused0: not used
//! \param[in] unused1: not used
void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    finish_compression_flag = true;
}

//! \brief the callback for setting off the router compressor
void initialise() {
    log_info("Setting up stuff to allow bitfield compressor to occur.");

    log_info("reading timer_for_compression_attempt");
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    timer_for_compression_attempt = sark_virtual_processor_info[
        spin1_get_core_id()].user1;
    compress_only_when_needed = sark_virtual_processor_info[
        spin1_get_core_id()].user2;
    compress_as_much_as_possible = sark_virtual_processor_info[
        spin1_get_core_id()].user3;

    spin1_set_timer_tick(timer_for_compression_attempt);
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER_TICK_PRIORITY);
    spin1_pause();

    log_info("set up sdp interrupt");
    spin1_callback_on(SDP_PACKET_RX, _sdp_handler, SDP_PRIORITY);
    log_info("finished sdp interrupt");

    log_info("set up sdp message bits");
    my_msg.srce_addr = spin1_get_chip_id();
    my_msg.dest_addr = spin1_get_chip_id();
    my_msg.srce_port = (RANDOM_PORT << PORT_SHIFT) | spin1_get_core_id();
    my_msg.data[COMMAND_CODE] = COMPRESSION_RESPONSE;
    my_msg.length = LENGTH_OF_SDP_HEADER + (
        LENGTH_OF_ACK_PACKET * WORD_TO_BYTE_MULTIPLIER);
    log_info("finished sdp message bits");
}

//! \brief the main entrance.
void c_main(void) {
    log_info("%u bytes of free DTCM", sark_heap_max(sark.heap, 0));

    initialise();

    // go
    spin1_start(SYNC_WAIT);
    //spin1_pause
    //spin1_resume
}
