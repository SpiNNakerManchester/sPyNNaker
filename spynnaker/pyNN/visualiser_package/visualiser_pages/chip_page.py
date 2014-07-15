__author__ = 'stokesa6'
import gtk
import math
import logging
from visualiser.abstract_page import AbstractPage
logger = logging.getLogger(__name__)


class ChipPage(AbstractPage):
    """this class allows a visual repesentation of a chip and the stuff thats
       been placed on this chip
    """

    LOGICAL_VIEW = 0
    PHYSICAL_VIEW = 1

    def __init__(self, chip, chip_placements, router_table, window_based=True):
        AbstractPage.__init__(self)
        self._chip = chip
        self._router_table = router_table
        self._coords = chip.get_coords()
        self._chip_placements = chip_placements
        #trakcer for subpop highlighting
        self.core_buttons = dict()
        self._window_based = window_based

        if window_based:  # needs to be in its own window and add its own tabs
            chip_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            #add a
            chip_window.connect("delete_event", self.delete_event)
            chip_window.set_border_width(10)
            chip_window.set_default_size(100, 100)
            chip_window.set_title("SpinnView Chip ({},{}) "
                                  "view".format(self._coords[0],
                                                self._coords[1]))
            chip_window.show()
            #add notebook for tabs of routing, cores,
            chip_pages = gtk.Notebook()
            chip_window.add(chip_pages)
            self._initilise_nootbook(chip_pages)
            self._core_table = gtk.Table(4, 5, True)
            self._core_table.show()
            chip_pages.append_page(self._core_table, gtk.Label("cores"))

        else:  # is in a page of some other window's tabs
            chip_page = gtk.Frame("")
            chip_page.show()
            # still needs its own tabs in a nested fashion
            chip_pages = gtk.Notebook()
            chip_page.add(chip_pages)
            self._initilise_nootbook(chip_pages)
            chip_page = gtk.Frame("cores")
            chip_page.show()
            chip_pages.append_page(chip_page, gtk.Label("cores"))
            self._core_table = gtk.Table(4, 3, True)
            chip_page.add(self._core_table)
        self._core_table.show()
        self._update_table(ChipPage.LOGICAL_VIEW)
        #create a routing page which contains routing entries
        routing_page = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        routing_page.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        routing_page.show()
        chip_pages.append_page(routing_page, gtk.Label("routing entries"))
        #locate the router table for this chip
        self._update_routing_table_page(routing_page, self._router_table)

    def is_page(self):
        return not self._window_based

    @staticmethod
    def _initilise_nootbook(chip_pages):
        chip_pages.show()
        chip_pages.show_tabs = True
        chip_pages.show_border = True
        chip_pages.set_tab_pos(gtk.POS_TOP)

    #method to kill#  the gui
    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def delete_event(self, widget, event, data=None):
        return False

    #creates a table of routing entries
    def _update_routing_table_page(self, routing_page, chip_router_table):
        entires_table = gtk.Table(7, 1001, False)

        entires_table.show()
        routing_page.add_with_viewport(entires_table)
        position = 1
        index_label = gtk.Label("Index  ")
        key_label = gtk.Label("Key (Hex)  ")
        mask_label = gtk.Label("Mask (Hex)  ")
        route_label = gtk.Label("Route (Hex)  ")
        source_label = gtk.Label("Src. Core  ")
        core_label = gtk.Label("-> [Cores][Links]")

        entires_table.attach(index_label, 0, 1, 0, 1, xoptions=gtk.SHRINK,
                             yoptions=gtk.SHRINK)
        entires_table.attach(key_label, 1, 2, 0, 1, xoptions=gtk.SHRINK,
                             yoptions=gtk.SHRINK)
        entires_table.attach(mask_label, 2, 3, 0, 1, xoptions=gtk.SHRINK,
                             yoptions=gtk.SHRINK)
        entires_table.attach(route_label, 3, 4, 0, 1, xoptions=gtk.SHRINK,
                             yoptions=gtk.SHRINK)
        entires_table.attach(source_label, 4, 5, 0, 1, xoptions=gtk.SHRINK,
                             yoptions=gtk.SHRINK)
        entires_table.attach(core_label, 5, 6, 0, 1, xoptions=gtk.SHRINK,
                             yoptions=gtk.SHRINK)

        for router_key in chip_router_table.keys():
            index_label = gtk.Label("{}".format(position - 1))
            key = int(chip_router_table[router_key][0].key)
            mask = int(chip_router_table[router_key][0].mask)
            route = int(chip_router_table[router_key][0].route)
            core_id = "({%d}, {%d}, {%d})".format((key >> 24 & 0xFF),
                                                  (key >> 16 & 0xFF),
                                                  (key >> 11 & 0xFF)+1)
            route_txt = self._expand_route_value(route)
            key_label = gtk.Label("{}".format(self.uint32_to_hex_string(key)))
            mask_label = gtk.Label("{}".format(self.uint32_to_hex_string(mask)))
            route_label = \
                gtk.Label("{}".format(self.uint32_to_hex_string(route)))
            source_label = gtk.Label("{}".format(core_id))
            core_label = gtk.Label("{}".format(route_txt))

            entires_table.attach(index_label, 0, 1, position, position + 1,
                                 xoptions=gtk.SHRINK)
            entires_table.attach(key_label, 1, 2, position, position + 1,
                                 xoptions=gtk.SHRINK)
            entires_table.attach(mask_label, 2, 3, position, position + 1,
                                 xoptions=gtk.SHRINK)
            entires_table.attach(route_label, 3, 4, position, position + 1,
                                 xoptions=gtk.SHRINK)
            entires_table.attach(source_label, 4, 5, position, position + 1,
                                 xoptions=gtk.SHRINK)
            entires_table.attach(core_label, 5, 6, position, position + 1,
                                 xoptions=gtk.SHRINK)
            position += 1

        entires_table.show()
        entires_table.show_all()

    @staticmethod
    def uint32_to_hex_string(number):
        """
        Convert a 32-bit unsigned number into a hex string.
        """
        bottom = number & 0xFFFF
        top = (number >> 16) & 0xFFFF
        hex_string = "%4.0X%4.0X" % (top, bottom)
        return hex_string

    @staticmethod
    def _expand_route_value(route_value):
        """
        Convert a 32-bit route word into a string which lists the target cores
        and links.
        """
        links_value = route_value & 0x3F
        processor_value = (route_value >> 6)
        # Convert processor targets to readable values:
        route_string = "["
        first = True
        for i in range(16):
            proc = processor_value & 0b1
            if proc != 0:
                if first:
                    route_string += "%d" % i
                    first = False
                else:
                    route_string += ", %d" % i
            processor_value >>= 1
        route_string += "] ["
        # Convert link targets to readable values:
        link_labels = {0: 'E', 1: 'NE', 2: 'N', 3: 'W', 4: 'SW', 5: 'S'}

        first = True
        for i in range(6):
            link = links_value & 0b1
            if link != 0:
                if first:
                    route_string += "%s" % link_labels[i]
                    first = False
                else:
                    route_string += ", %s" % link_labels[i]
            links_value >>= 1
        route_string += "]"

        return route_string

    # updates the table with core layout
    def _update_table(self, view):
        if view == ChipPage.PHYSICAL_VIEW:
            core_ids = [4, 12, 13, 5, 0, 8, 9, 1, 16, None, None, 17, 6, 14,
                        15, 7, 2, 10, 11, 3]
            count = 0
            for core_id in core_ids:
                if core_id is None:
                    count += 1
                else:
                    button = gtk.Button("({})".format(core_id))
                    processor = self._chip.processors[core_id]
                    this_placement = None
                    for placement in self._chip_placements:
                        if placement.processor == processor:
                            this_placement = placement
                    if processor.placement is not None:
                        subvert = this_placement.subvertex

                        button.set_tooltip_text("id : {}. \n {} to {}."
                                                .format(subvert.vertex.label,
                                                        subvert.lo_atom,
                                                        subvert.hi_atom))
                    else:
                        button.set_tooltip_text("this core does not "
                                                "contain any atoms")
                    button.show()
                    button.set_sensitive(False)
                    y = int(math.floor(count / 4))
                    x = int(count - (y * 4))
                    self._core_table.attach(button, x, x+1, y, y+1)
                    self.core_buttons[core_ids[count]] = button
                    count += 1
        else:
            for core_id in range(19):
                button = gtk.Button("({})".format(core_id))
                if core_id >= 16 or core_id == 0:
                    button.set_tooltip_text("this core is not avilable "
                                            "for use in pacman103")
                else:
                    processor = self._chip.processors[core_id]
                    found = False
                    for placement in self._chip_placements:
                        if placement.processor == processor:
                            subvert = placement.subvertex
                            vertex = placement.subvertex.vertex

                            button.set_tooltip_text("id : {}. \n  {} to {}."
                                                    .format(vertex.label,
                                                            subvert.lo_atom,
                                                            subvert.hi_atom))
                            found = True
                    if not found:
                        button.set_tooltip_text("this core does not "
                                                "contain any atoms")
                button.show()
                button.set_sensitive(False)
                y = int(math.floor(core_id / 4))
                x = int(core_id - (y * 4))
                self._core_table.attach(button, x, x+1, y, y+1)
                self.core_buttons[core_id] = button

    def update_table(self, option):
        for button_key in self.core_buttons.keys():
            button = self.core_buttons[button_key]
            self._core_table.remove(button)
        print "options is {}".format(option)
        if option:
            self._update_table(ChipPage.LOGICAL_VIEW)
        else:
            self._update_table(ChipPage.PHYSICAL_VIEW)
