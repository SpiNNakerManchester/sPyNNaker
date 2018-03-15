BUILDS = spike_source/poisson delay_extension neuron robot_motor_control

all: 
	python convertor.py $(abspath src) $(abspath modified_src) messages.txt || exit $$?; done
	for d in $(BUILDS:%=modified_src/%); do $(MAKE) -C $$d || exit $$?; done

%.aplx: %
	"$(MAKE)" -C $*

%.aplx: neuron/builds/%
	"$(MAKE)" -C neuron/builds/$*

clean: 
	for d in $(BUILDS:%=src/%); do $(MAKE) -C $$d clean || exit $$?; done
	rm -r $(abspath modified_src) || true
