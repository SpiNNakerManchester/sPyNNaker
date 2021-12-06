Changes for PyNN0.9 and Neo0.5
------------------------------
This document covers only the differences noticed between PyNN0.8 and PyNN0.9, which includes a change from Neo0.4 to Neo0.5.

For a more complete list of differences please see the PyNN or Neo documentation.

No full numpy compatibility
---------------------------
The `v`, `gsyn_exc`, `gsyn_inh` data returned by

- `neo.segment[0].filter(name=name)[0]`
- `segment.filter(name=name)[0]`

which is an `AnalogSignal`, and no longer guarantees full Neo support.

For example [slice behaves different](https://github.com/NeuralEnsemble/python-neo/issues/407)

Our suggestion is to obtain the inner data object using
- `AnalogSignal.magnitude` for a pure numpy array
- `AnalogSignal.as_quantity()` for a 2d quantity array which includes units

AnalogSignal
------------
The class `AnalogSignalArray` has been removed.
Instead the class `AnalogSignal` can now hold data for multiple types.

Also the `Segment` will now store these in the property analogsignals rather than analogsignalarrays.

setup max_delay
---------------
The `max_delay` parameter is no longer passed to pure pynn's supported.

It is still part of sPyNNaker's setup but will cause an error if the script is used outside of sPyNNaker.

channel_index
-------------
The `AnalogSignal`'s channel_index property is now a `ChannelIndex` object.

To get a list of indexes do: `signal_array.channel_index.index`

Backward Compatability
----------------------
Currently the code will also work if *both* PyNN version 0.8 and Neo version 0.4 are installed.

However the PyNN and Neo developers no longer support PyNN 0.8 and Neo 0.4 and have asked everyone to upgrade as soon as possible.

Therefore support of PyNN0.8 will probably be dropped soon and even before support for PyNN0.7.
Please contact us urgently to say why you need PyNN0.8 and therefore Neo 0.4 to be supported.
