#include <spin1_api.h>
#include <debug.h>
#include <bit_field.h>
#include <sdp_no_scp.h>
#include "common-typedefs.h"
#include "../common/compressor_common/platform.h"
#include "../common/compressor_common/routing_table.h"
#include "../common/compressor_common/compression_sdp_formats.h"
#include "../common/compressor_common/aliases.h"
#include "../common/compressor_common/ordered_covering.h"
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

//! interrupt priorities
typedef enum interrupt_priority{
    TIMER_TICK_PRIORITY = -1, SDP_PRIORITY = 1, COMPRESSION_START_PRIORITY = 2
} interrupt_priority;

//! word to byte multiplier
#define WORD_TO_BYTE_MULTIPLIER 4

//! timeout for sdp message attempt
#define _SDP_TIMEOUT 100

//! random port as 0 is in use by scamp/sark
#define RANDOM_PORT 4

//! max length of the router table entries
#define TARGET_LENGTH 1023

//! \brief the timer control logic.
bool* timer_for_compression_attempt = false;

//! \brief number of times a compression time slot has occurred
bool* finish_compression_flag = false;

//! \brief bool flag to say if i was forced to stop by the compressor control
bool* finished_by_compressor_force = false;

//! bool flag pointer to allow minimise to report if it failed due to malloc
//! issues
bool* failed_by_malloc = false;

//! control flag for running compression only when needed
bool compress_only_when_needed = false;

//! control flag for compressing as much as possible
bool compress_as_much_as_possible = false;

//! \brief the sdram location to write the compressed router table into
address_t sdram_loc_for_compressed_entries;

//! \brief store for addresses for routing entries in sdram
table_t** routing_tables;

//! how many packets waiting for
uint32_t number_of_packets_waiting_for = 0;

//! the number of addresses currently stored
uint32_t n_tables = 0;

//! \brief the control core id for sending responses to
uint32_t control_core_id = 0;

//! \brief sdp message to send acks to the control core with
sdp_msg_pure_data my_msg;

//! \brief sends a sdp message back to the control core
void send_sdp_message_response(){
    my_msg.dest_port = control_core_id;
    // send sdp packet
    while (!spin1_send_sdp_msg((sdp_msg_t *) &my_msg, _SDP_TIMEOUT)) {
        // Empty body
    }
}

//! \brief send a failed response due to a malloc issue
void return_malloc_response_message(){
    // set message ack finished state to malloc fail
    my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA] = FAILED_MALLOC;

    // send message
    send_sdp_message_response();
}

//! \brief send a success response message
void return_success_response_message(){
    // set message ack finished state to malloc fail
    my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA] = SUCCESSFUL_COMPRESSION;

    // send message
    send_sdp_message_response();
}

//! \brief send a failed response due to the control forcing it to stop
void return_failed_by_force_response_message(){
       // set message ack finished state to malloc fail
    my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA] = FORCED_BY_COMPRESSOR_CONTROL;

    // send message
    send_sdp_message_response();
}

//! \brief sends a failed response due to running out of time
void return_failed_by_time_response_message(){
       // set message ack finished state to malloc fail
    my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA] = RAN_OUT_OF_TIME;

    // send message
    send_sdp_message_response();
}

//! \brief send a failed response where finished compression but failed to
//! fit into allocated size.
void return_failed_by_space_response_message(){
       // set message ack finished state to malloc fail
    my_msg.data[START_OF_SPECIFIC_MESSAGE_DATA] = FAILED_TO_COMPRESS;

    // send message
    send_sdp_message_response();
}

//! \brief stores the compressed routing tables into the compressed sdram
//! location
//! \returns bool if was successful or now
bool store_into_compressed_address(){
    return true;
}

//! \brief starts the compression process
void start_compression_process(){
    // reset fail state flags
    *failed_by_malloc = false;
    *timer_for_compression_attempt = false;
    *finished_by_compressor_force = false;

    // create aliases
    aliases_t aliases = aliases_init();

    // run compression
    bool success = oc_minimise(
        routing_tables, n_tables, TARGET_LENGTH, &aliases, failed_by_malloc,
        finished_by_compressor_force, timer_for_compression_attempt,
        finish_compression_flag, compress_only_when_needed,
        compress_as_much_as_possible);

    // check state
    if (success){
        success = store_into_compressed_address();
        if (success){
            return_success_response_message();
        }
        else{
            return_failed_by_space_response_message();
        }
    }
    else{  // if not a success, could be one of 4 states
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
//! \param[in] mailbox: the message
//! \param[in] port: don't care.
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

        start_stream_sdp_packet_t* first_command_packet =
            (start_stream_sdp_packet_t*)
            msg->data[START_OF_SPECIFIC_MESSAGE_DATA];

        // location where to store the compressed (size
        sdram_loc_for_compressed_entries =
            first_command_packet->address_for_compressed;

        // set up fake heap
        log_info("setting up fake heap for sdram usage");
        platform_new_heap_creation(first_command_packet->fake_heap_data);
        log_info("finished setting up fake heap for sdram usage");

        // set up packet tracker
        number_of_packets_waiting_for =
            first_command_packet->n_sdp_packets_till_delivered;

        number_of_packets_waiting_for -= 1;

        // set up addresses data holder
        log_info(
            "allocating %d bytes for %d total n tables",
            first_command_packet->total_n_tables * sizeof(table_t**),
            first_command_packet->total_n_tables);
        routing_tables = MALLOC(
            first_command_packet->total_n_tables * sizeof(table_t**));

        if (routing_tables == NULL){
            log_error(
                "failed to allocate memory for holding the addresses "
                "locations");
            sark_msg_free((sdp_msg_t*) msg);
            return_malloc_response_message();
        }
        else{

            // store this set into the store
            log_info("store routing table addresses into store");
            for(uint32_t rt_index = 0; rt_index <
                    first_command_packet->n_tables_in_packet; rt_index++){
                routing_tables[rt_index] =
                    first_command_packet->tables[rt_index];
            }

            // keep tracker updated
            n_tables += first_command_packet->n_tables_in_packet;
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
        if (routing_tables == NULL){
            log_error(
                "ignoring extra routing table addresses packet, as cant store"
                " them");
        }
        else{

            extra_stream_sdp_packet_t* extra_command_packet =
                (extra_stream_sdp_packet_t*) msg->data[
                    START_OF_SPECIFIC_MESSAGE_DATA];

            // store this set into the store
            log_info("store extra routing table addresses into store");
            for(uint32_t rt_index = 0; rt_index <
                    extra_command_packet->n_tables_in_packet;
                    rt_index++){
                routing_tables[rt_index] =
                    extra_command_packet->tables[rt_index];
            }
            log_info("finished storing extra routing table address into store");


            // keep tracker updated
            n_tables += extra_command_packet->n_tables_in_packet;
            number_of_packets_waiting_for -= 1;

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
        *finished_by_compressor_force = true;
        sark_msg_free((sdp_msg_t*) msg);
    }
}

//! \brief timer interrupt for controlling time taken to try to compress table
//! \param[in] unused0: not used
//! \param[in] unused1: not used
void timer_callback(uint unused0, uint unused1) {
    use(unused0);
    use(unused1);
    *finish_compression_flag = true;
}

//! \brief the callback for setting off the router compressor
void initialise() {
    log_info("Setting up stuff to allow bitfield compressor to occur.");

    log_info("reading time_for_compression_attempt");
    vcpu_t *sark_virtual_processor_info = (vcpu_t*) SV_VCPU;
    uint32_t time_for_compression_attempt = sark_virtual_processor_info[
        spin1_get_core_id()].user1;

    // bool from int conversion happening here
    int int_value = sark_virtual_processor_info[spin1_get_core_id()].user2;
    if (int_value == 0){
        compress_only_when_needed = true;
    }

    int_value = sark_virtual_processor_info[spin1_get_core_id()].user3;
    if (int_value == 0){
        compress_as_much_as_possible = true;
    }

    spin1_set_timer_tick(time_for_compression_attempt);
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
        sizeof(response_sdp_packet_t) * WORD_TO_BYTE_MULTIPLIER);
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
