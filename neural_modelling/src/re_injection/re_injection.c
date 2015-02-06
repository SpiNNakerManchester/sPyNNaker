// SARK-based program
#include <sark.h>
#include "spin1_api.h"
#include "../common/common-impl.h"
// ------------------------------------------------------------------------
// constants
// ------------------------------------------------------------------------
#define TICK_PERIOD        10      // attempt to bounce dumped packets
#define PKT_QUEUE_SIZE     256     // dumped packet queue length

#define ROUTER_SLOT        SLOT_0  // router VIC slot -- not used currently!
#define CC_SLOT            SLOT_1  // comms. cont. VIC slot
#define TIMER_SLOT         SLOT_2  // timer VIC slot

#define RTR_BLOCKED_BIT    25
#define RTR_DOVRFLW_BIT    30
#define RTR_DENABLE_BIT    2

#define RTR_BLOCKED_MASK   (1 << RTR_BLOCKED_BIT)   // router blocked
#define RTR_DOVRFLW_MASK   (1 << RTR_DOVRFLW_BIT)   // router dump overflow
#define RTR_DENABLE_MASK   (1 << RTR_DENABLE_BIT)   // enable dump interrupts

#define PKT_CONTROL_SHFT   16
#define PKT_PLD_SHFT       17
#define PKT_TYPE_SHFT      22
#define PKT_ROUTE_SHFT     24

#define PKT_CONTROL_MASK   (0xff << PKT_CONTROL_SHFT)
#define PKT_PLD_MASK       (1 << PKT_PLD_SHFT)
#define PKT_TYPE_MASK      (3 << PKT_TYPE_SHFT)
#define PKT_ROUTE_MASK     (7 << PKT_ROUTE_SHFT)

#define PKT_TYPE_MC        (0 << PKT_TYPE_SHFT)
#define PKT_TYPE_PP        (1 << PKT_TYPE_SHFT)
#define PKT_TYPE_NN        (2 << PKT_TYPE_SHFT)
#define PKT_TYPE_FR        (3 << PKT_TYPE_SHFT)

#define TIMER2_CONF        0x82
#define TIMER2_LOAD        0
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// types
// ------------------------------------------------------------------------
typedef struct  // dumped packet type
{
  uint hdr;
  uint key;
  uint pld;
} packet_t;


typedef struct  // packet queue type
{
  uint head;
  uint tail;
  packet_t queue[PKT_QUEUE_SIZE];
} pkt_queue_t;
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// global variables
// ------------------------------------------------------------------------
uint coreID;

uint rtr_control;
uint cc_sar;

uint pkt_ctr0;
uint pkt_ctr1;
uint pkt_ctr2;
uint pkt_ctr3;

uint max_time;
static uint32_t time = UINT32_MAX;

pkt_queue_t pkt_queue;  // dumped packet queue
// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// functions
// ------------------------------------------------------------------------


INT_HANDLER timer_int_han (void)
{
  //#ifdef DEBUG
   // // count entries //##
   // sark.vcpu->user2++;
  //#endif

  // clear interrupt in timer,
  //tc[T1_INT_CLR] = (uint) tc;

  // check if router not blocked
  if ((rtr[RTR_STATUS] & RTR_BLOCKED_MASK) == 0)
  {
    // access packet queue with fiq disabled,
    uint cpsr = cpu_fiq_disable ();

    // if queue not empty turn on packet bouncing,
    if (pkt_queue.tail != pkt_queue.head)
    {
      // restore fiq after queue access,
      cpu_int_restore (cpsr);

      // enable comms. cont. interrupt to bounce packets
      vic[VIC_ENABLE] = 1 << CC_TNF_INT;
    }
    else
    {
      // restore fiq after queue access,
      cpu_int_restore (cpsr);
    }
  }

 // #ifdef DEBUG
    // update packet counters,
    //##  sark.vcpu->user0 = pkt_ctr0;
   // sark.vcpu->user1 = pkt_ctr1;
    //##  sark.vcpu->user2 = pkt_ctr2;
    //##  sark.vcpu->user3 = pkt_ctr3;
  //#endif

  // and tell VIC we're done
  //vic[VIC_VADDR] = (uint) vic;
}

void timer_init (uint period)
{
  // set up count-down mode,
  tc[T1_CONTROL] = 0xe2;

  // load time in microsecs,
  tc[T1_LOAD] = sark.cpu_clk * period;

  // and configure VIC slot
  sark_vic_set (TIMER_SLOT, TIMER1_INT, 1, timer_int_han);
}


INT_HANDLER router_int_han (void)
{
  // clear interrupt in router,
  (void) rtr[RTR_STATUS];

  // get packet from router,
  uint hdr = rtr[RTR_DHDR];
  uint pld = rtr[RTR_DDAT];
  uint key = rtr[RTR_DKEY];

  // bounce mc packets only
  if ((hdr & PKT_TYPE_MASK) == PKT_TYPE_MC)
  {
    // try to insert dumped packet in the queue,
    uint new_tail = (pkt_queue.tail + 1) % PKT_QUEUE_SIZE;

    // check for space in the queue
    if (new_tail != pkt_queue.head)
    {
      // queue packet,
      pkt_queue.queue[pkt_queue.tail].hdr = hdr;
      pkt_queue.queue[pkt_queue.tail].key = key;
      pkt_queue.queue[pkt_queue.tail].pld = pld;

      // update queue pointer,
      pkt_queue.tail = new_tail;
    }
  }
}


INT_HANDLER cc_int_han (void)
{
  //TODO: may need to deal with packet timestamp.

  // check if router not blocked
  if ((rtr[RTR_STATUS] & RTR_BLOCKED_MASK) == 0)
  {
    // access packet queue with fiq disabled,
    uint cpsr = cpu_fiq_disable ();

    // if queue not empty bounce packet,
    if (pkt_queue.tail != pkt_queue.head)
    {
      // dequeue packet,
      uint hdr = pkt_queue.queue[pkt_queue.head].hdr;
      uint pld = pkt_queue.queue[pkt_queue.head].pld;
      uint key = pkt_queue.queue[pkt_queue.head].key;

      // update queue pointer,
      pkt_queue.head = (pkt_queue.head + 1) % PKT_QUEUE_SIZE;

      // restore fiq after queue access,
      cpu_int_restore (cpsr);

      // write header and route,
      cc[CC_TCR] = hdr & PKT_CONTROL_MASK;
      cc[CC_SAR] = cc_sar | (hdr & PKT_ROUTE_MASK);

      // maybe write payload,
      if (hdr & PKT_PLD_MASK)
      {
        cc[CC_TXDATA] = pld;
      }

      // write key to fire packet,
      cc[CC_TXKEY] = key;

      #ifdef DEBUG
        // count entries //##
        sark.vcpu->user3++;

        // and count packet
        //# pkt_ctr3++;
      #endif
    }
    else
    {
      // restore fiq after queue access,
      cpu_int_restore (cpsr);

      // and disable comms. cont. interrupts
      vic[VIC_DISABLE] = 1 << CC_TNF_INT;
    }
  }
  else
  {
    // disable comms. cont. interrupts
    vic[VIC_DISABLE] = 1 << CC_TNF_INT;
  }

  // and tell VIC we're done
  vic[VIC_VADDR] = (uint) vic;
}

void router_init ()
{
  // re-configure wait values in router
  rtr[RTR_CONTROL] = (rtr[RTR_CONTROL] & 0x0000ffff) | 0x004f0000;

  // configure fiq vector,
  sark_vec->fiq_vec = router_int_han;

  // configure as fiq,
  vic[VIC_SELECT] = 1 << RTR_DUMP_INT;

  // enable interrupt,
  vic[VIC_ENABLE] = 1 << RTR_DUMP_INT;

  // clear router interrupts,
  (void) rtr[RTR_STATUS];

  // clear router dump status,
  (void) rtr[RTR_DSTAT];

  // and enable router interrupts when dumping packets
  rtr[RTR_CONTROL] |= (1 << RTR_DENABLE_BIT);
}


void cc_init ()
{
  // remember SAR register contents (p2p source ID)
  cc_sar = cc[CC_SAR] & 0x00ff;

  // configure VIC slot -- don't enable yet!
  sark_vic_set (CC_SLOT, CC_TNF_INT, 0, cc_int_han);
}


// Callbacks
void timer_callback (uint unused0, uint unused1)
{
    use(unused0);
    use(unused1);
    time++;

    //log_info("Timer tick %d", time);
    if (time == 1){

         cc_init ();                // setup comms. cont. interrupt when not full

        router_init ();            // setup router to interrupt when dumping
    }

    if (simulation_ticks != UINT32_MAX &&
        time == simulation_ticks + timer_period)
    {
        log_info("Simulation complete.\n");
        // and disable comms. cont. interrupts
        vic[VIC_DISABLE] = 1 << CC_TNF_INT;
         // enable interrupt,
        vic[VIC_DISABLE] = 1 << RTR_DUMP_INT;
        log_info("turned off the inturrupts");
        spin1_exit(0);
        return;
    }
    //timer_int_han();
}

// ------------------------------------------------------------------------


// ------------------------------------------------------------------------
// main
// ------------------------------------------------------------------------

static bool load_dtcm()
{
    log_info("load_dtcm: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = system_load_sram();
    system_load_params(region_start(0, address));
    return true;
}


void c_main()
{
    log_info("initializing dumped packet bouncer\n");
    bool ans;
    // Configure system
    ans = load_dtcm();
    if (!ans) return;

    //adjust the simulation tic counter to take into accoutn higher burn rate
    simulation_ticks *= 100;

    // Set timer_callback
    spin1_set_timer_tick(TICK_PERIOD);
    spin1_callback_on (TIMER_TICK, timer_callback, 2);

    log_info("starting dumped packet bouncer\n");
    system_runs_to_completion();
    log_info("exited dumped packet bouncer\n");
}
// ------------------------------------------------------------------------