BUILDS = live_spike_recorder spike_source/array spike_source/poisson delay_extension neuron multicast_source robot_motor_control
DIRS = $(BUILDS:%=src/%)

all: $(DIRS)
	for d in $(DIRS); do (cd $$d; "$(MAKE)") || exit $$?; done

%.aplx: %
	cd $*; "$(MAKE)"

%.aplx: neuron/builds/%
	cd neuron/builds/$*; "$(MAKE)"

clean: $(DIRS)
	for d in $(DIRS); do (cd $$d; "$(MAKE)" clean) || exit $$?; done
