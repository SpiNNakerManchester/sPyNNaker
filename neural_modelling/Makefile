BUILDS = live_packet_gather spike_source/array spike_source/poisson delay_extension neuron command_sender_multicast_source robot_motor_control reverse_iptag_multicast_source re_injection
DIRS = $(BUILDS:%=src/%)

all: $(DIRS)
	for d in $(DIRS); do (cd $$d; "$(MAKE)") || exit $$?; done

%.aplx: %
	cd $*; "$(MAKE)"

%.aplx: neuron/builds/%
	cd neuron/builds/$*; "$(MAKE)"

clean: $(DIRS)
	for d in $(DIRS); do (cd $$d; "$(MAKE)" clean) || exit $$?; done
