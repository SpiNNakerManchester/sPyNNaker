#include "delay_sender.h"
#include <common-typedefs.h>
#include <debug.h>
#include <spin1_api.h>
#include <stdbool.h>
#include <delay_extension/delay_extension.h>

extern void spin1_wfi();
extern void configure_timer1(uint time, uint phase);

#define TIMER_TICK_VALUE 1000000
#define MAX_DELAYS_PER_PACKET 127
#define MAX_SEQUENCE 0xFFFF

static sdp_msg_t delay_message;
static uint16_t *delay_message_sequence;
static uint16_t *delay_message_n_delays;
static uint16_t *delay_message_delays;
static uint16_t chip_id;
static uint16_t core_id;
static uint16_t delays[MAX_DELAYS_PER_PACKET];
static uint32_t n_delays;
static uint16_t sequence = MAX_SEQUENCE;
static bool response_received = true;

static void _handle_sdp_message(uint mailbox, uint sdp_port) {
    use(sdp_port);
    sdp_msg_t *msg = (sdp_msg_t *) mailbox;
    uint16_t *data = (uint16_t *) &(msg->cmd_rc);
    log_info("\t\tACK %u from 0x%04x %u, waiting for %u from 0x%04x %u", data[0], msg->srce_addr, msg->srce_port, sequence, delay_message.dest_addr, delay_message.dest_port);
    if (data[0] == sequence && msg->srce_addr == delay_message.dest_addr &&
            msg->srce_port == delay_message.dest_port) {
        response_received = true;
    }
    spin1_msg_free(msg);
}

static void _handle_timeout(uint unused0, uint unused1) {
    // Does Nothing - just used to detect timeout
    use(unused0);
    use(unused1);
    log_info("Timeout");
}

void delay_sender_initialize(uint32_t delay_chip, uint32_t delay_core) {
    n_delays = 0;
    chip_id = delay_chip;
    core_id = delay_core;

    // initialise SDP header
    delay_message.tag = 0;
    delay_message.flags = 0x07;
    delay_message.dest_addr = delay_chip;
    delay_message.dest_port = (1 << PORT_SHIFT) | delay_core;
    delay_message.srce_addr = spin1_get_chip_id();
    delay_message.srce_port = (1 << PORT_SHIFT) | spin1_get_core_id();
    uint16_t *data = &delay_message.cmd_rc;
    delay_message_sequence = &(data[0]);
    delay_message_n_delays = &(data[1]);
    delay_message_delays = &(data[2]);

    spin1_set_timer_tick(TIMER_TICK_VALUE + (spin1_get_core_id() * 3));

    spin1_callback_on(SDP_PACKET_RX, _handle_sdp_message, 0);
    spin1_callback_on(TIMER_TICK, _handle_timeout, -1);
}

static void wait_for_delay_response() {

    log_info("Waiting for response %u", sequence);

    // Wait until the response to the last message has been received
    while (!response_received) {

        // Wait for a time for a response
        spin1_resume(SYNC_NOWAIT);
        spin1_wfi();
        spin1_pause();

        // Re-send the message
        if (!response_received) {
            log_info("Sending message");
            while (!spin1_send_sdp_msg(&delay_message, 10)) {

                // Do Nothing
            }
            log_info("Message Sent");
        }
    }
}

void delay_sender_flush() {
    uint32_t n_delays_to_send = n_delays;
    n_delays = 0;
    uint32_t offset = 0;
    while (n_delays_to_send > 0) {
        wait_for_delay_response();

        uint16_t n_delays_in_packet = n_delays_to_send;
        if (n_delays_in_packet > MAX_DELAYS_PER_PACKET) {
            n_delays_in_packet = MAX_DELAYS_PER_PACKET;
        }

        n_delays_to_send -= n_delays_in_packet;

        delay_message.length =
            sizeof(sdp_hdr_t) + sizeof(uint16_t) + sizeof(uint16_t) +
            (sizeof(uint16_t) * n_delays_in_packet);

        response_received = false;
        sequence = sequence + 1;
        *delay_message_sequence = sequence;
        *delay_message_n_delays = n_delays_in_packet;
        spin1_memcpy(
            delay_message_delays, &(delays[offset]),
            sizeof(uint16_t) * n_delays_in_packet);
        log_info(
            "Sending %u of %u delays to 0x%04x, %u, sequence %u",
            n_delays_in_packet, n_delays, chip_id, core_id, sequence);
        spin1_send_sdp_msg(&delay_message, 1);
        offset += n_delays_in_packet;
    }
}

void delay_sender_send(uint32_t index, uint32_t stage) {
    delays[n_delays++] = pack_delay_index_stage(index, stage);
    if (n_delays >= MAX_DELAYS_PER_PACKET) {
        delay_sender_flush();
    }
}

void delay_sender_close() {
    if (n_delays > 0) {
        delay_sender_flush();
        wait_for_delay_response();
    }
    sequence = sequence + 1;
    response_received = false;
    log_info("Sending end message %u to 0x%04x, %u", sequence, chip_id, core_id);
    *delay_message_sequence = sequence;
    *delay_message_n_delays = 0;
    delay_message.length =
        sizeof(sdp_hdr_t) + sizeof(uint16_t) + sizeof(uint16_t);
    spin1_send_sdp_msg(&delay_message, 1);
    wait_for_delay_response();
    spin1_callback_off(SDP_PACKET_RX);
    spin1_callback_off(TIMER_TICK);
}
