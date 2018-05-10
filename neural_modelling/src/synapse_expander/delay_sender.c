#include "delay_sender.h"
#include <common-typedefs.h>
#include <debug.h>
#include <spin1_api.h>
#include <stdbool.h>
#include <delay_extension/delay_extension.h>

#define SLEEP_TIME 10000
#define MAX_DELAYS_PER_PACKET 127

static bool delay_response_received = true;
static sdp_msg_t delay_message;
static uint16_t chip_id;
static uint16_t core_id;
static uint16_t delays[MAX_DELAYS_PER_PACKET];
static uint32_t n_delays;

static void _handle_sdp_message(uint mailbox, uint sdp_port) {
    use(mailbox);
    use(sdp_port);
    log_info("\t\tACK received");
    delay_response_received = true;
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

    spin1_callback_on(SDP_PACKET_RX, _handle_sdp_message, 1);
}

static void wait_for_delay_response() {

    // Wait until the response to the last message has been received
    while (!delay_response_received) {

        // Wait for a time for a response
        log_debug("Waiting for response from last delay message");
        spin1_delay_us(SLEEP_TIME);

        // Re-send the message
        if (!delay_response_received) {
            spin1_send_sdp_msg(&delay_message, 1);
        }
    }
}

void delay_sender_flush() {
    uint32_t n_delays_to_send = n_delays;
    uint32_t offset = 0;
    while (n_delays_to_send > 0) {
        wait_for_delay_response();
        delay_response_received = false;

        uint32_t n_delays_in_packet = n_delays_to_send;
        if (n_delays_in_packet > MAX_DELAYS_PER_PACKET) {
            n_delays_in_packet = MAX_DELAYS_PER_PACKET;
        }

        n_delays_to_send -= n_delays_in_packet;

        delay_message.length =
            sizeof(sdp_hdr_t) + sizeof(uint32_t) +
            (sizeof(uint16_t) * n_delays_in_packet);

        uint16_t *data = &delay_message.cmd_rc;
        data[0] = (uint16_t) n_delays_in_packet;
        spin1_memcpy(
            &(data[1]), &(delays[offset]),
            sizeof(uint16_t) * n_delays_in_packet);
        spin1_send_sdp_msg(&delay_message, 1);

        log_debug(
            "Sending %u of %u delays to 0x%04x, %u",
            n_delays_in_packet, n_delays, chip_id, core_id);
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
    delay_response_received = false;
    log_debug("Sending end message to 0x%04x, %u", chip_id, core_id);
    delay_message.cmd_rc = 0;
    delay_message.length = sizeof(sdp_hdr_t) + sizeof(uint32_t);
    spin1_send_sdp_msg(&delay_message, 1);
    wait_for_delay_response();
    return;
}
