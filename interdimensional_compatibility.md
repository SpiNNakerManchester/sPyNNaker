Interdimensional Compatibility
==============================

The software has been enhanced to support multi-dimensional vertices, and the
communication between these vertices which might have different dimensionality.
The order of the neurons in a Population with more than one dimension have been
chosen to be a [Raster Scan](https://en.wikipedia.org/wiki/Raster_scan) of the
neurons through each dimension e.g. in a 2D Population, the pixels are ordered
in a rows starting from top-left, where neuron 0 is (0, 0) to bottom-right where
neuron n is (w, h), where w is the width and h is the height of the Population
of n = (w x h) neurons.

This means that the user does not have to consider how the neurons are split
over the cores. The mapping should account for this internally.  Some of how
this is achieved is described below.

Splitting into cores
--------------------
When a 1-dimensional Population is split over multiple cores, it is simply split
up so that each core has a fixed number of neurons, defined by the maximum
number of neurons per core.  The last core may have less neurons if the size is
such that it does not divide by this number.  For example, with 10 neurons per
core, a 30 neuron Population will be divided into 3 cores made up of neurons
(0-9), (10-19) and (20-29), where a 25 neuron Population will be divided into 3
cores also but made up of neurons (0-9), (10-19) and (20-24), so there will only
be 5 neurons on the last core.  By default, the number of neurons per core is
256.

When a multi-dimensional Population is split over multiple cores, it will
generally be split into hyper-rectangles i.e. n-dimensional rectangles, where
each dimension is given a maximum number of neurons per core.  The restriction
here is that each dimension must be exactly divisible by the number of neurons
per core in that dimension.  For example, a Population with size (10, 10) in 2
dimensions (so having 100 neurons) can be split into (5, 5) neurons per core
made up of rectangles (in this case squares) of neurons (0,0 - 5,5),
(0,6 - 5,10), (6,0 - 10,5) and (6,6 - 10,10).

Population Keys
---------------
When a neuron in a Population spikes, it sends a key that represents the index
of the neuron in the Population.  Each Population is given a Population-level
key, and then each core is given a core index within the Population.  These
are assigned in bit fields in the overall key so that they can be added
together, along with the neuron index on the core, to make the full key.
This is shown below.

`|Population key|Core index|Neuron index|`

The neuron index is a raster scan of the neurons on the core regardless of the
dimensionality of the Population, in the same way that the Population neuron
indices are a raster scan of the neurons of the Population through the
dimensions.  As the key structure is always the same regardless of the
dimensionality, the Populations can communicate even if their dimensionalities
do not match.  The trick is then to ensure that the synaptic information is
organised to perform the correct mapping when the key is received.

Synaptic Mapping
----------------
When a key is received, the receiving vertex should not have to process it. The
aim is that the rows are ordered such that the key can be used to say which row
of the synaptic table to look at by simple calculation.  The calculation for the
row index from the key is:
`(core_n * neurons_per_core) + core_neuron`

The values of `core_n` and `core_neuron` can be determined from the received
key (`core_n` from the `core index` part and `core_neuron` from the
`neuron index` part.  The `neurons_per_core` can be stored on the core
using the `population key`, and so can be looked up on key reception.

When the source and target are linear Populations, the mapping between the row
index above and the pre-neuron index is simply one-to-one. When the source and
target have the same number of dimensions, neurons-per-core and size, the same
is true.  When the source and target differ in any of these aspects, the mapping
is more complicated.  The trick then is to calculate the row index from each
pre-neuron index so that the information for that pre-neuron can be stored in
at the appropriate row index.

In addition to this, we also have to split the information on each synaptic
row into the appropriate target cores.  Again, for simple linear mapping this
is a one-to-one value.  For a n-dimensional target though, the splitting is
again more complicated, but again can be calculated so that the final indices
in the row are those of neurons on the local core with no further calculation
required when the key is received.

#### To `row index` from `pre-neuron index`
`full_size[n]`: The full size of the Population in the n'th dimension

`neurons_per_core[n]`: The number of neurons per core in the n'th dimension

`total_neurons_per_core`: The total number of neurons per core

`cores_per_size[n]`: The number of cores of the Population in the n'th
dimension; this is a shorthand for `full_size[n] / neurons_per_core[n]`
(which must be an integer value by design).

`neuron_pos[n]`: The global position of the neuron in the n'th dimension

`core_index[n]`: The core index in the n'th dimension.

`raster_core_index`: The core index after core rasterization.

`neuron_index[n]`: The local neuron index in the n'th dimension.

`raster_neuron_index`: The local neuron index after rasterization.

```
# Work out the position of the neuron in each dimension
remainder = pre_neuron_index
last_size = 1
for n in n_dimensions:
    neuron_pos[n] = remainder // last_size
    remainder -= neuron_pos[n] * last_size
    last_size = full_size[n]

# Work out which core the pre-neuron is on in each dimension
for n in n_dimensions:
    core_index[n] = neuron_pos[n] / neurons_per_core[n]

# Work out the raster-index of the core
raster_core_index = 0;
last_size = 0;
for n in n_dimensions:
    raster_core_index = (raster_core_index * last_size) + core_index[n]
    last_size = cores_per_size[n]

# Work out which index the pre-neuron is on the core in each dimension
for n in n_dimensions:
    neuron_index[n] = neuron_pos[n] - (neurons_per_core[n] * core_index[n])

# Work out the raster-index of the pre-neuron on the core
raster_neuron_index = 0
last_size = 0
for n in n_dimensions:
    raster_neuron_index = (raster_neuron_index * last_size) + neuron_index[n]
    last_size = neurons_per_core[n]

# Work out the row index from the above and the neurons-per-core
row_index = (raster_core_index * total_neurons_per_core) + raster_neuron_index
```

#### To `local neuron index` from `population neuron index`


Multidimensional Connectors
---------------------------
In contrast to the above, it is sometimes more useful to find the coordinates
of a pre-neuron from its key rather than the row index.  An example of this
is when doing convolution processing, where the rows are not explicitly
computed, but instead the mapping is calculated when the key is received.  For
this type of mapping, it is useful to be able to work out the pre-neuron index
from the key first, and then compute the coordinates of that key.
