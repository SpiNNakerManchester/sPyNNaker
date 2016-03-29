

class SPyNNakerProvenanceWriter(object):
    """ Gets provenance data from sPyNNaker objects
    """

    def __call__(self, projections, provenance_data_objects=None):

        if provenance_data_objects is not None:
            prov_items = provenance_data_objects
        else:
            prov_items = list()

        # get data from the projection
        for projection in projections:
            prov_items.extend(projection.get_provenance_data())

        return {'prov_items': prov_items}
