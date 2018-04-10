# BUILDS = spike_source/poisson delay_extension neuron_make_files robot_motor_control
BUILDS = spike_source/poisson
DIRS = $(BUILDS:%=src/%)

all: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d || exit $$?; done

%.aplx: %
	"$(MAKE)" -C $*

%.aplx: neuron/builds/%
	"$(MAKE)" -C neuron/builds/$*

clean: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d clean || exit $$?; done
