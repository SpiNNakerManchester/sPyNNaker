BUILDS = spike_source/poisson delay_extension neuron robot_motor_control
DIRS = $(BUILDS:%=modified_src/%)

all: $(DIRS)
	-python convertor.py $(abspath src) $(abspath modified_src)
	for d in $(DIRS); do $(MAKE) -C $$d || exit $$?; done

%.aplx: %
	"$(MAKE)" -C $*

%.aplx: neuron/builds/%
	"$(MAKE)" -C neuron/builds/$*

clean: $(DIRS)
	for d in $(DIRS); do $(MAKE) -C $$d clean || exit $$?; done
