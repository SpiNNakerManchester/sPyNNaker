from spynnaker.pyNN.models.abstract_models.abstract_master_pop_table_factory\
    import AbstractMasterPopTableFactory
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities.utility_calls \
    import get_region_base_address_offset
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN import exceptions

#dsg imports
from data_specification.enums.data_type import DataType

import logging
logger = logging.getLogger(__name__)


class MasterPopTableAsBinaryTree(AbstractMasterPopTableFactory):

    def __init__(self):
        AbstractMasterPopTableFactory.__init__(self)