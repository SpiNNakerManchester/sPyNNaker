BUILDS = spike_source/poisson delay_extension neuron robot_motor_control

all: 
	python -m spinn_utilities.make_tools.convertor $(abspath src) $(abspath modified_src) 3000 || exit $$?; done
	for d in $(BUILDS:%=modified_src/%); do $(MAKE) -C $$d || exit $$?; done

%.aplx: %
	"$(MAKE)" -C $*

%.aplx: neuron/builds/%
	"$(MAKE)" -C neuron/builds/$*

convert:
	rm -r $(abspath modified_src) || true
	python -m spinn_utilities.make_tools.convertor $(abspath src) $(abspath modified_src) 3000 || exit $$?; done

clean: 
	for d in $(BUILDS:%=src/%); do $(MAKE) -C $$d clean || exit $$?; done
	rm -r $(abspath modified_src) || true
