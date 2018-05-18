#include <stdbool.h>
#include <debug.h>
#include <data_specification.h>
#include <bit_field.h>
#include <delay_extension/delay_extension.h>

// The number of post vertices
static uint32_t n_post_vertices;

// The number of post vertices that have completed
static uint32_t n_post_vertices_finished = 0;

// The list of post vertices that have completed to check for duplicates
static uint32_t *post_vertices_finished;

static uint32_t num_neurons;

static uint32_t num_delay_stages;

static uint32_t neuron_bit_field_words;

static bit_field_t *neuron_delay_stage_config;

static void read_params(address_t address) {
    n_post_vertices = address[N_OUTGOING_EDGES];
    post_vertices_finished = spin1_malloc(n_post_vertices * sizeof(uint32_t));
    sark_word_set(
        post_vertices_finished, 0, n_post_vertices * sizeof(uint32_t));
    log_debug("%u post vertices", n_post_vertices);

    num_neurons = address[N_ATOMS];
    neuron_bit_field_words = get_bit_field_size(num_neurons);
    num_delay_stages = address[N_DELAY_STAGES];
    neuron_delay_stage_config = (bit_field_t *) address[DELAY_BLOCKS];
}

// Sends an acknowledgement response to an SDP
static void send_ack_response(sdp_msg_t *msg) {
    msg->length = sizeof(sdp_hdr_t) + sizeof(uint16_t);
    uint dest_port = msg->dest_port;
    uint dest_addr = msg->dest_addr;
    msg->dest_port = msg->srce_port;
    msg->srce_port = dest_port;
    msg->dest_addr = msg->srce_addr;
    msg->srce_addr = dest_addr;
    log_info("Sending ACK of %u to 0x%04x, %u", msg->cmd_rc, msg->dest_addr, msg->dest_port);
    while (!spin1_send_sdp_msg(msg, 10)) {
        // Do Nothing
    }
}

// Handle an incoming SDP message
void handle_sdp_message(uint mailbox, uint port) {
    use(port);

    // Read the message
    sdp_msg_t *msg = (sdp_msg_t *) mailbox;
    uint16_t *data = (uint16_t *) &(msg->cmd_rc);
    uint16_t n_delays = data[1];

    // If the number of delays is 0, this is a finish message
    if (n_delays == 0) {

        uint32_t source = (msg->srce_addr << 16) | (msg->srce_port & 0x1F);

        // Send a response to say the message was received
        send_ack_response(msg);

        // Check if the source has been seen before
        bool seen = false;
        for (uint32_t i = 0; i < n_post_vertices_finished; i++) {
            if (source == post_vertices_finished[i]) {
                seen = true;
                break;
            }
        }

        // Free the message as no longer needed
        spin1_msg_free(msg);

        // If the source hasn't been seen, mark it as finished
        if (!seen) {
            post_vertices_finished[n_post_vertices_finished] = source;
            n_post_vertices_finished += 1;
            log_info(
                "%u of %u post vertices complete",
                n_post_vertices_finished, n_post_vertices);
            if (n_post_vertices_finished == n_post_vertices) {
                log_info("All post vertices complete: exiting");
                sark_cpu_state(CPU_STATE_EXIT);
            }
        }
        return;
    }

    // Otherwise, continue reading
    log_info("Reading %u delays from 0x%04x, %u",
            n_delays, msg->srce_addr, msg->srce_port);

    uint16_t *delays = (uint16_t *) &(data[2]);
    for (uint32_t i = 0; i < n_delays; i++) {
        uint8_t neuron_id = unpack_delay_index(delays[i]);
        uint8_t stage = unpack_delay_stage(delays[i]);
        log_info(
            "Delay %u, source neuron id = %u, delay stage = %u",
            i, neuron_id, stage);
        bit_field_set(neuron_delay_stage_config[stage], neuron_id);
    }

    // Send the acknowledgement
    send_ack_response(msg);

    // Free the message
    spin1_msg_free(msg);
}

void c_main() {

    // Process the parameters
    address_t core_address = data_specification_get_data_address();
    address_t delay_address = data_specification_get_region(
        DELAY_PARAMS, core_address);
    read_params(delay_address);

    // Wait for SDP messages
    spin1_callback_on(SDP_PACKET_RX, handle_sdp_message, 1);
    spin1_start(SYNC_NOWAIT);
}
