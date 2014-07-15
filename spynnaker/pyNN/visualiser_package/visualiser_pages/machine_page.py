__author__ = 'stokesa6'
import math
import logging

import gtk
import pygtk

logger = logging.getLogger(__name__)
pygtk.require('2.0')
from visualiser.abstract_page import AbstractPage
from spynnaker.pyNN.visualiser_package.visualiser_pages.chip_page \
    import ChipPage


class MachinePage(AbstractPage):

    CHIP_SCOPE = "chip"
    CORE_SCOPE = "core"

    def __init__(self, static, scope, machine, placements, router_tables):
        AbstractPage.__init__(self)
        self._current_button_right_clicked = None
        self._button_mapping = dict()
        self._chips_with_views = dict()
        self._machine_table = None
        self._x_dim = machine.dimensions['x']
        self._y_dim = machine.dimensions['y']
        self._placements = placements
        self._router_tables = router_tables
        self._machine = machine
        if static:
            self._label = "machine static"
            self.page = gtk.Frame(self._label)
        else:
            self._label = "machine"
            self.page = gtk.Frame(self._label)
        self._create_machine_page_content(scope)
        if not static:
            pass

    @property
    def label(self):
        return self._label

    def is_page(self):
        return True

     #creates the machien table with edges and cores
    def _create_machine_page_content(self, scope):
        #set out table so that it sues double the reuqirements for edges
        self._machine_table = gtk.Table(self._x_dim, self._y_dim, True)
        self._machine_table.set_col_spacings(0)
        self._machine_table.set_row_spacings(0)
        self.page.add(self._machine_table)
        self._machine_table.show()
        #set up buttons to represent cores
        self._set_up_chips_in_machine(scope)
        #add the edges
        self._add_edges()

    #updates page with new machine layout
    def update_page(self, scope):
        for key in self._button_mapping.keys():
            button = self._button_mapping[key][2]
            self._machine_table.remove(button)
        self._button_mapping = dict()
        self._set_up_chips_in_machine(scope)
        self._machine_table.queue_draw()

    #sets up all the chips in the machine view from the dao (uses buttons)
    def _set_up_chips_in_machine(self, scope):
        for x in range(self._x_dim):
            for y in range(self._y_dim):

                column_y = self._correct_y_pos(y, self._y_dim)
                column_x = self._correct_x_pos(x)

                if scope == MachinePage.CHIP_SCOPE:
                    button = gtk.Button("({},{})".format(x, y))
                    #check if button represents a valid chip
                    self._check_button_state(button, x, y)
                    #attach button to table
                    self._machine_table.attach(button, column_x, column_x + 1,
                                               column_y, column_y + 1)
                    #create right click menu
                    menu = self._create_right_click_menu()
                    #add the coords into the hash so we
                    #  can track which chip is being considered
                    self._button_mapping[menu] = {'x': x, 'y': y, 'b': button}
                    # connect the listener for the button
                    button.connect_object("event", self._button_press, menu)
                else:
                    if self._machine.does_chip_exist_at_xy(x, y):
                        core_table = gtk.Table(4, 4, False)
                        core_table.show()

                        self._machine_table.attach(core_table, column_x,
                                                   column_x + 1, column_y,
                                                   column_y + 1)
                        core_ids = [4, 12, 13, 5, 0, 8, 9, 1, 16, None, None,
                                    17, 6, 14, 15, 7, 2, 10, 11, 3]
                        count = 0
                        for core_id in core_ids:
                            if core_id is None:
                                count += 1
                            else:
                                button = gtk.Button("({})".format(core_id))
                                button.show()
                                button.set_sensitive(False)
                                y = int(math.floor(count / 4))
                                x = int(count - (y * 4))
                                core_table.attach(button, x, x + 1, y, y + 1)
                                key = x + y + core_ids[count]
                                self._button_mapping[key] = {'x': x, 'y': y,
                                                             'b': button}
                                button.connect("enter-notify-event",
                                               self._population_data,
                                               [x, y, core_ids[count]])
                                count += 1

    @staticmethod
    def _population_data():
        print ""

    @staticmethod
    def _correct_y_pos(machine_y, table_size):
        return table_size - (machine_y * 2) - 2

    @staticmethod
    def _correct_x_pos(machine_x):
        return (machine_x * 2) + 1

    # creates the menu used in right clicks
    @staticmethod
    def _create_right_click_menu():
        menu = gtk.Menu()
        menu.show()
        tab_menu_item = gtk.MenuItem("chip view in new tab")
        tab_menu_item.show()
        tab_menu_item.connect("activate", "tab")
        window_menu_item = gtk.MenuItem("chip view in new window")
        window_menu_item.connect("activate", "win")
        window_menu_item.show()
        menu.append(tab_menu_item)
        menu.append(window_menu_item)
        return menu

    # handles the response from the right clicked menu
    def _menuitem_response(self, menu_type):
        chip_coords = self._button_mapping[self._current_button_right_clicked]
        self._chips_with_views[chip_coords[0] + chip_coords[1]] = ChipPage
        chip = self._machine.get_chip_at_location(chip_coords)
        if menu_type == "win":
            ChipPage(chip, self._placements.get_placment_by_chip(chip_coords),
                     self._router_tables.get_router_table_by_chip(chip_coords),
                     True)
        elif menu_type == "tab":
            ChipPage(chip, self._placements.get_placment_by_chip(chip_coords),
                     self._router_tables.get_router_table_by_chip(chip_coords),
                     False)

    #handles the clicking of a chip button (either set up right click menu or
    # opens up chip view in new window
    def _button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self._current_button_right_clicked = widget
            widget.popup(None, None, None, event.button, event.time)
            return True
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            chip_coords = self._button_mapping[widget]
            self._chips_with_views[chip_coords[0] + chip_coords[1]] = ChipPage
            ChipPage(self._machine.get_chip_at_location({'x': chip_coords[0],
                                                         'y': chip_coords[1]}),
                     self._placements.get_placment_by_chip(chip_coords),
                     self._router_tables.get_router_table_by_chip(chip_coords),
                     True)
        return False

    #checks the state of the chip being repsented in the dao, if not real, then
    #turn to blakc and disable the button
    def _check_button_state(self, button, x, y):
        if self._machine.does_chip_exist_at_xy(x, y):
            button.show()
        else:
            color_map = button.get_colormap()
            color = color_map.alloc_color("black")
            style = button.get_style().copy()
            button.set_sensitive(False)

            style.bg[gtk.STATE_NORMAL] = color
            button.set_style(style)
            button.show()

    #handles edge placement in the table
    def _add_edges(self):
        x_dim = self._machine.dimenions('x')
        y_dim = self._machine.dimenions('y')
        adjustments = ({'x': 1, 'y': 0}, {'x': 1, 'y': 1}, {'x': 1, 'y': 0},
                       {'x': -1, 'y': 0}, {'x': -1, 'y': -1}, {'x': 0, 'y': -1})
                         #E        NE      N        W        SW       S
        for x in range(x_dim):
            for y in range(y_dim):
                if self._machine.chip_exists_at_xy(x, y):
                    index = 0
                    chip = self._machine.get_chip(x, y)
                    for connection in chip.router.neighbourlist:
                        #calculate edge position
                        column_y = \
                            self._correct_y_pos(y, self._y_dim) + \
                            adjustments[index]['y']
                        column_x =\
                            self._correct_x_pos(x) + adjustments[index]['x']
                        #attach in correct position
                        if connection is not None:
                            if index == 0:  # E, W
                                self._machine_table.attach(gtk.Label("-"),
                                                           column_x,
                                                           column_x + 1,
                                                           column_y,
                                                           column_y + 1)
                            if index == 1:  # ne sw
                                self._machine_table.attach(gtk.Label("/"),
                                                           column_x,
                                                           column_x + 1,
                                                           column_y - 2,
                                                           column_y - 1)
                            if index == 2:  # N s
                                self._machine_table.attach(gtk.Label("|"),
                                                           column_x - 1,
                                                           column_x,
                                                           column_y - 1,
                                                           column_y)

                        index += 1
        self._machine_table.show_all()

    def update_chip_layout(self, option):
        for chip_view_key in self._chips_with_views.keys():
            chip_view = self._chips_with_views[chip_view_key]
            chip_view.update(chip_view, option)