BUILDS = spike_source/poisson delay_extension neuron robot_motor_control connection_builder delay_extension_receiver
DIRS = $(BUILDS:%=src/%)

all: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d || exit $$?; done

%.aplx: %
	"$(MAKE)" -C $*

%.aplx: neuron/builds/%
	"$(MAKE)" -C neuron/builds/$*

clean: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d clean || exit $$?; done
