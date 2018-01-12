#include "src/common/neuron-typedefs.h"
#include "src/common/in_spikes.h"
#include "delay_block.h"

#include <bit_field.h>
#include <data_specification.h>
#include <debug.h>
#include <simulation.h>
#include <spin1_api.h>

#include <string.h>

//#define DEBUG_MESSAGES

static uint32_t tick_count;

// Constants
#define MAX_DELAY  16
#define SDRAM_TAG 160
#define CLEAR_MEMORY_FLAG 0x55555555
#define DELAY_PARAMS 1
#define SLEEP_TIME 4711

enum parameter_positions {
    KEY, INCOMING_KEY, INCOMING_MASK, N_ATOMS, N_DELAY_STAGES,
    RANDOM_BACKOFF, TIME_BETWEEN_SPIKES, DELAY_BLOCKS
};

// Globals
static uint32_t done_receiving = false;

static uint32_t num_neurons = 0;
static uint32_t num_delay_stages = 0;
static uint32_t neuron_bit_field_words = 0;
static uint32_t* delay_block = NULL;

void clear_memory(uint32_t memory_size, uint32_t *syn_mtx_addr){
    for(uint32_t w = 0; w < memory_size; w++){
        syn_mtx_addr[w] = 0;
    }

}

// Sends an acknowledgement response to an SDP
static void send_ack_response(sdp_msg_t *msg) {
//#ifdef DEBUG_MESSAGES
    log_info("ACK to 0x%04x.%02u:%u,", msg->srce_addr,
             msg->srce_port &((1 << PORT_SHIFT) - 1), msg->srce_port >> PORT_SHIFT);
//#endif

    uint8_t *data = &msg->cmd_rc;
    data[0] = RC_OK;
    msg->length = sizeof(sdp_hdr_t) + 1;
    uint8_t  old_dest_port = msg->dest_port;
    uint16_t old_dest_addr = msg->dest_addr;

    msg->dest_port = msg->srce_port;
    msg->dest_addr = msg->srce_addr;

    msg->srce_port = old_dest_port;
    msg->srce_addr = old_dest_addr;

    if(spin1_send_sdp_msg(msg, 1) == 0){
        log_info("Failed to send Acknowledge Message!");
    }
    spin1_delay_us(3+sark_core_id());

}

//TODO*** define this somewhere else!
#define BUILD_IN_MACHINE_PORT 1
#define BUILD_IN_MACHINE_TAG  111
//TODO - END

void handle_sdp_message(uint mailbox, uint port) {

    if(port != BUILD_IN_MACHINE_PORT){
        return;
    }
    // Read the message
    sdp_msg_t *msg = (sdp_msg_t *) mailbox;
    uint16_t *data = &(msg->cmd_rc);
    uint16_t n_delays = data[0];
    uint16_t pre_slice_start = data[1];

//    log_info("n delays %u\tpre slice start %u", n_delays, pre_slice_start);
    if (n_delays == 0) {
//        log_info("\tAll delays received");
        // Send a response to say the message was received
        spin1_delay_us(SLEEP_TIME + spin1_get_core_id());
        send_ack_response(msg);

        // Free the message as no longer needed
        spin1_msg_free(msg);
//        done_receiving = true;
//        spin1_delay_us(1000);
//        sark_cpu_state(CPU_STATE_EXIT);
//        spin1_exit(0);
//        return;
    }
    else if (n_delays <= 100){

        uint32_t state = spin1_irq_disable();
        // Otherwise, continue reading
//        log_info("%u delays\tpre start %u", n_delays, pre_slice_start);

        delay_msg_t *delays = (delay_msg_t *) &(data[2]);
//        log_info("delay_block address = 0x%08x", delay_block);

        for (uint32_t i = 0; i < n_delays; i++) {
            uint32_t delay_shift = 1;
            if(delays[i].delay%MAX_DELAY == 0){ delay_shift++; }
            uint32_t stage = delays[i].delay/MAX_DELAY - delay_shift;
#ifdef DEBUG_MESSAGES
            log_info("\tPre id %u, delay %u, stage %u",
                     delays[i].source_neuron_id, delays[i].delay, stage);
#endif
            if (delays[i].delay == 0){
                log_info("Delay = 0? What happened?");
                break;
            }
            bit_field_set(delay_block + stage*neuron_bit_field_words,
                          delays[i].source_neuron_id);

        }
//        for(uint32_t i = 0; i < num_delay_stages; i++){
//            log_info("delay_block[%u] = 0x%08x", i, delay_block[i] );
//        }
        // Send the acknowledgement
//        send_ack_response(msg);
        spin1_mode_restore(state);

        // Free the message
        spin1_delay_us(SLEEP_TIME + spin1_get_core_id());
        send_ack_response(msg);

        spin1_msg_free(msg);
    }


}

void app_start(uint a0, uint a1){
    use(a0);
    use(a0);
    sark_cpu_state(CPU_STATE_RUN);

    uint32_t *clear_memory_ptr = (uint32_t *)sark_tag_ptr(SDRAM_TAG + spin1_get_core_id(),
                                                          sark_app_id());


    // Initialise
    address_t core_address = data_specification_get_data_address();
    address_t delay_address = data_specification_get_region(DELAY_PARAMS, core_address);
    log_info("delay_address = 0x%08x", delay_address);

//    for(uint32_t i = 0; i < 16; i++){
//        log_info("data at row %u = %u", i, delay_address[i]);
//    }

    num_neurons = delay_address[N_ATOMS];
    neuron_bit_field_words = get_bit_field_size(num_neurons);
    num_delay_stages = delay_address[N_DELAY_STAGES];

    log_info("num_neurons = %d, neuron_bit_field_words = %d, num_delay_stages = %d",
              num_neurons, neuron_bit_field_words, num_delay_stages);
    delay_block = (uint32_t *)(&delay_address[DELAY_BLOCKS]);
    log_info("delay_block address = 0x%08x", delay_block);

    if( *clear_memory_ptr == CLEAR_MEMORY_FLAG){
        log_info("Clearing Memory in Delay Extension Receiver");

        clear_memory(neuron_bit_field_words*num_delay_stages, delay_block);
    }

    sark_xfree (sv->sdram_heap, clear_memory_ptr, ALLOC_LOCK);

    log_info("Waiting for delay messages");

}

// Entry point
void c_main(void) {

    // Set timer tick (in microseconds)
    spin1_schedule_callback(app_start, 0, 0, 2);
    spin1_callback_on(SDP_PACKET_RX, handle_sdp_message, 1);

    spin1_start(SYNC_NOWAIT);
    // sark_cpu_state(CPU_STATE_RUN);

}
