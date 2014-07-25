import logging
import gtk
from spynnaker.pyNN.visualiser_package.visualiser_pages.raster_page \
    import RasterPage
from spynnaker.pyNN.visualiser_package.visualiser_pages.topological_page\
    import TopologicalPage
from spynnaker.pyNN.utilities import conf

import visualiser.visualiser_constants as visualiser_modes
from visualiser.abstract_page import AbstractPage

logger = logging.getLogger(__name__)


class ConfigPage(AbstractPage):

    RASTER_TEXT = "Raster_view"
    TOPOLOGICAL_TEXT = "Topological view"
    NOT_SET_TEXT = "Not set yet"
    INDIVIDUAL_RASTER_TEXT = "add as an individual raster plot"
    MERGED_RASTER_TEXT = "add to combination raster plot"

    def __init__(self, vertex_mapper, visualiser_vertexes, graph,
                 container, transciever, has_board, sim_runtime,
                 machine_time_step, subgraph, placements):
        AbstractPage.__init__(self)
        self._vertex_mapper = vertex_mapper
        self._drop_box_mapper = dict()
        self._raster_combo_box_selection = dict()
        self._main_combo_box_selection = dict()
        #set name of page
        self._label = "population_config_page"
        self._config_page = gtk.Frame(self._label)
        self._container = container
        self._transciever = transciever
        self._has_board = has_board
        self._sim_run_time = sim_runtime
        self._machine_time_step = machine_time_step
        self._subgraph = subgraph
        self._placements = placements

        #get vertexes which are set to record
        self._visual_vertexes = visualiser_vertexes
        self._graph = graph

        #set a table layout for the data
        self._table = gtk.Table(4, len(self._visual_vertexes) + 1, True)
        self._table.set_col_spacings(0)
        self._table.set_row_spacings(0)
        self._config_page.add(self._table)
        #add the vertex to the table
        self._add_vertexes()

        self._config_page.show_all()
        
    def is_page(self):
        return False

    @property
    def label(self):
        """returns the label of the page
        :return: a string reprensetation of teh page
        :rtype: str
        :raise None: Does not raise any known errors
        """
        return self._label

    def _add_vertexes(self):
        """
        goes though each vertex and adds its configurations options
        """
        #go though the vertexes and create a label and a dropbox box
        position = 0
        for vertex in self._visual_vertexes:
            self._table.attach(gtk.Label(vertex.vertex.label), 0, 1,
                               position, position + 1)
            self._handle_first_tier_combos(vertex, position)
            position += 1

    def _handle_first_tier_combos(self, vertex, position):
        """
        deals with combo boxes and config options
        """
        combo_box = gtk.ComboBox()
        liststore = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        combo_box.pack_start(cell)
        combo_box.add_attribute(cell, 'text', 0)
        combo_box.set_wrap_width(5)
        liststore.append([self.RASTER_TEXT])
        liststore.append([self.TOPOLOGICAL_TEXT])
        liststore.append([self.NOT_SET_TEXT])
        # set model and connect tro response method
        combo_box.set_model(liststore)
        combo_box.connect('changed', self._changed_main_cb)
        self._add_to_mapper(combo_box, vertex, position, 1)
        self._table.attach(combo_box, 1, 2, position, position+1)
        #set active value to the one from defaults
        mode = vertex.visualiser_mode
        if mode == visualiser_modes.RASTER:
            self._main_combo_box_selection[position] = 0
            combo_box.set_active(0)
        elif mode == visualiser_modes.TOPOLOGICAL:
            combo_box.set_active(1)
            self._main_combo_box_selection[position] = 1
        else:
            self._main_combo_box_selection[position] = 2
            combo_box.set_active(2)
        return mode

    def _add_to_mapper(self, mappable_object, vertex, position, x):
        """updates the object tracker for removals and mapping to vertexes
        """
        self._drop_box_mapper[mappable_object] = dict()
        self._drop_box_mapper[mappable_object]['v'] = vertex
        self._drop_box_mapper[mappable_object]['p'] = position
        self._drop_box_mapper[mappable_object]['x'] = x

    def _changed_main_cb(self, combo_box):
        """handles the modification of the config table based on the
        choice made by the main entry combo box. This includes the removal of
        old entries in the table
        """
        model = combo_box.get_model()
        index = combo_box.get_active()
        data = self._drop_box_mapper[combo_box]
        if (index > -1 and
           (data['p'] not in self._main_combo_box_selection.keys() or
           index != self._main_combo_box_selection[data['p']])):

            self._main_combo_box_selection[data['p']] = index
            selected = model[index][0]

            if selected == self.TOPOLOGICAL_TEXT:
                data['v'].visualiser_raster_seperate = None
                data['v'].visualiser_mode = visualiser_modes.TOPOLOGICAL
                text_box = gtk.Entry()
                if (data['v'].visualiser_2d_dimensions is not None and
                   data['v'].visualiser_2d_dimensions['x'] is not None):
                    text_box.set_text(str(data['v'].
                                      visualiser_2d_dimensions['x']))
                object_to_remove = self._locate_object(data['x']+1, data['p'])
                if object_to_remove is not None:
                    self._table.remove(object_to_remove)
                    del self._drop_box_mapper[object_to_remove]
                self._add_to_mapper(text_box, data['v'], data['p'], data['x']+1)
                text_box.connect("activate", self._added_x_dimension)
                self._table.attach(text_box, data['x']+1, data['x']+2,
                                   data['p'], data['p']+1)
                text_box = gtk.Entry()
                if (data['v'].visualiser_2d_dimensions is not None and
                   data['v'].visualiser_2d_dimensions['y'] is not None):
                    text_box.set_text(str(data['v'].
                                      visualiser_2d_dimensions['y']))
                object_to_remove = self._locate_object(data['x']+2, data['p'])
                if object_to_remove is not None:
                    self._table.remove(object_to_remove)
                    del self._drop_box_mapper[object_to_remove]
                self._add_to_mapper(text_box, data['v'], data['p'], data['x']+2)
                text_box.connect("activate", self._added_y_dimension)
                self._table.attach(text_box, data['x']+2, data['x']+3,
                                   data['p'], data['p']+1)
            elif selected == self.RASTER_TEXT:
                data['v'].visualiser_2d_dimensions = {'x': None, 'y': None}
                data['v'].visualiser_mode = visualiser_modes.RASTER
                liststore = gtk.ListStore(str)
                combo_box = gtk.ComboBox(liststore)
                cell = gtk.CellRendererText()
                combo_box.pack_start(cell)
                combo_box.add_attribute(cell, 'text', 0)
                combo_box.set_wrap_width(5)
                liststore.append([self.INDIVIDUAL_RASTER_TEXT])
                liststore.append([self.MERGED_RASTER_TEXT])
                liststore.append([self.NOT_SET_TEXT])
                raster_mode = data['v'].visualiser_raster_seperate
                if raster_mode is None:
                    self._raster_combo_box_selection[data['p']] = 2
                    combo_box.set_active(2)
                elif raster_mode:
                    self._raster_combo_box_selection[data['p']] = 0
                    combo_box.set_active(0)
                else:
                    self._raster_combo_box_selection[data['p']] = 1
                    combo_box.set_active(1)

                object_to_remove = self._locate_object(data['x']+1, data['p'])
                if object_to_remove is not None:
                    self._table.remove(object_to_remove)
                    del self._drop_box_mapper[object_to_remove]
                self._add_to_mapper(combo_box, data['v'], data['p'],
                                    data['x']+1)
                self._table.attach(combo_box, data['x']+1, data['x']+2,
                                   data['p'], data['p']+1)
                combo_box.connect('changed', self._changed_raster_choice_cb)
                label = gtk.Label("")
                object_to_remove = self._locate_object(data['x']+2, data['p'])
                if object_to_remove is not None:
                    self._table.remove(object_to_remove)
                    del self._drop_box_mapper[object_to_remove]
                self._add_to_mapper(label, data['v'], data['p'], data['x']+2)
                self._table.attach(label, data['x']+2, data['x']+3, data['p'],
                                   data['p']+1)
            else:
                data['v'].visualiser_2d_dimensions = {'x': None, 'y': None}
                data['v'].visualiser_raster_seperate = None
                data['v'].visualiser_mode = None
                label = gtk.Label("")
                data['v'].visualiser_2d_dimensions = {'x': None, 'y': None}
                object_to_remove = self._locate_object(data['x']+1, data['p'])
                if object_to_remove is not None:
                    self._table.remove(object_to_remove)
                    del self._drop_box_mapper[object_to_remove]
                self._add_to_mapper(label, data['v'], data['p'], data['x']+1)
                self._table.attach(label, data['x']+1, data['x']+2, data['p'],
                                   data['p']+1)
                label = gtk.Label("")
                object_to_remove = self._locate_object(data['x']+2, data['p'])
                if object_to_remove is not None:
                    self._table.remove(object_to_remove)
                    del self._drop_box_mapper[object_to_remove]
                self._add_to_mapper(label, data['v'], data['p'], data['x']+2)
                self._table.attach(label, data['x']+2, data['x']+3, data['p'],
                                   data['p']+1)
            self._table.show_all()
            self._update_pages(selected, data['v'])

    def _update_pages(self, main_combo_selection, vertex):
        """
        updates all the pages so that they reflect decisions made by the config
        page
        """
        if ((main_combo_selection == self.NOT_SET_TEXT and
           vertex in self._vertex_mapper.keys())):
                self._remove_page(vertex)
        elif ((main_combo_selection == self.RASTER_TEXT and
              vertex in self._vertex_mapper.keys())):
                associated_page = self._vertex_mapper[vertex]
                if isinstance(associated_page, TopologicalPage):
                    self._remove_page(vertex)
        elif vertex in self._vertex_mapper.keys():  # topological position
            associated_page = self._vertex_mapper[vertex]
            if isinstance(associated_page, RasterPage):
                self._container.remove_page(associated_page._page)

    def _locate_object(self, x, y):
        """
        locates an obhect given the x and y coords
        """
        for key in self._drop_box_mapper.keys():
            mappable_object = self._drop_box_mapper[key]
            if mappable_object['x'] == x and mappable_object['p'] == y:
                return key

    def _changed_raster_choice_cb(self, combo_box):
        """

        handle the changes made by the raster combo box, this includes
        making new pages and removing old pages as nessacry
        """
        raster_plot_x_scope = \
            conf.config.get("Visualiser", "raster_plot_x_scope")
        raster_plot_do_fading = \
            conf.config.getboolean("Visualiser", "raster_plot_do_fading")

        model = combo_box.get_model()
        index = combo_box.get_active()
        data = self._drop_box_mapper[combo_box]
        if -1 < index != self._raster_combo_box_selection[data['p']]:
            selected = model[index][0]
            if selected == self.INDIVIDUAL_RASTER_TEXT:
                if data['v'] in self._vertex_mapper.keys():
                    associated_page = self._vertex_mapper[data['v']]
                    if (isinstance(associated_page, RasterPage)
                       and associated_page.is_merged_version):
                        self._remove_page(data['v'])
                        raster_page =\
                            RasterPage(
                                data['v'], raster_plot_x_scope,
                                raster_plot_do_fading, self._sim_run_time,
                                self._machine_time_step, self._transciever,
                                self._has_board, merged=False)
                        self._vertex_mapper[data['v']] = raster_page
                    else:
                        pass  # page already exists
                else:  # dont have a associated page
                    raster_page = RasterPage(
                        data['v'], raster_plot_x_scope, raster_plot_do_fading,
                        self._sim_run_time, self._machine_time_step,
                        self._transciever, self._has_board, merged=False)
                    self._vertex_mapper[data['v']] = raster_page
            elif selected == self.MERGED_RASTER_TEXT:  # merged
                if data['v'] in self._vertex_mapper.keys():
                    associated_page = self._vertex_mapper[data['v']]
                    if (isinstance(associated_page, RasterPage)
                       and associated_page.is_merged_version):
                        pass  # already in merged page
                    elif isinstance(associated_page, RasterPage):
                        self._remove_page(data['v'])
                        located = False
                        for page in self._container.main_pages:
                            if (isinstance(page, RasterPage)
                               and page.is_merged_version):
                                page.add_vertex(data['v'])
                                self._vertex_mapper[data['v']] = page
                                located = True
                        if not located:
                            raster_page = RasterPage(
                                data['v'], raster_plot_x_scope,
                                raster_plot_do_fading, self._sim_run_time,
                                self._machine_time_step, self._transciever,
                                self._has_board, merged=True)
                            self._vertex_mapper[data['v']] = raster_page
                else:  # no page set currently for the vertex,
                # locate any merged page and add it to it
                    found = False
                    for page in self._container.main_page:
                        if (isinstance(page, RasterPage)
                           and page.is_merged_version):
                            found = True
                            page.add_vertex(data['v'])
                            self._vertex_mapper[data['v']] = page
                    if not found:  # no merged page found
                        raster_page = RasterPage(
                            data['v'], raster_plot_x_scope,
                            raster_plot_do_fading, self._sim_run_time,
                            self._machine_time_step, self._transciever,
                            self._has_board, merged=True)
                        self._vertex_mapper[data['v']] = raster_page
            else:  # not set
                if data['v'] in self._vertex_mapper.keys():
                    self._remove_page(data['v'])
        self._raster_combo_box_selection[data['p']] = index

    def _added_x_dimension(self, entry_box):
        """
        method that updates the x dimension of the vertex dimensions assuming
        its given valid input
        """
        retina_drop_off_theshold = \
            conf.config.get("Visualiser",
                            "retina_plot_drop_off_value_per_sec")

        text = entry_box.get_text()
        try:
            int_value = int(text)
            data = self._drop_box_mapper[entry_box]
            vertex = data['v']
            dimensions = vertex.visualiser_2d_dimensions
            vertex.visualiser_2d_dimensions = {'x': int_value,
                                               'y': dimensions['y']}
            #x isnt none otherwise we wouldnt have reached here
            if dimensions['y'] is not None:
                #already had a topological page
                if dimensions['x'] is not None:
                    self._remove_page(data['v'])
                    retina_page = \
                        TopologicalPage(vertex, retina_drop_off_theshold,
                                        self._subgraph, self._placements,
                                        self._has_board, self._transciever)
                    self._vertex_mapper[vertex] = retina_page
                else:
                    #create a topological view
                    retina_page = \
                        TopologicalPage(vertex, retina_drop_off_theshold,
                                        self._subgraph, self._placements,
                                        self._has_board, self._transciever)
                    #update tracker
                    self._vertex_mapper[vertex] = retina_page
        except ValueError:
            logger.info("entered text thats not "
                        "convertable into a integer, ignoring")
            pass

    def _added_y_dimension(self, entry_box):
        """
        method that updates the y dimension of the vertex dimensions assuming
        its given valid input
        """
        retina_drop_off_theshold = \
            conf.config.get("Visualiser",
                            "retina_plot_drop_off_value_per_sec")

        text = entry_box.get_text()
        try:
            int_value = int(text)
            data = self._drop_box_mapper[entry_box]
            vertex = data['v']
            dimensions = vertex.visualiser_2d_dimensions
            vertex.visualiser_2d_dimensions = {'y': int_value,
                                               'x': dimensions['x']}
             #x isnt none otherwise we wouldnt have reached here
            if dimensions['x'] is not None:
                #already had a topological page
                if dimensions['y'] is not None:
                    self._remove_page(data['v'])

                    retina_page =\
                        TopologicalPage(vertex, retina_drop_off_theshold,
                                        self._subgraph, self._placements,
                                        self._has_board, self._transciever)
                    self._vertex_mapper[vertex] = retina_page
                else:
                    #create a topological view
                    retina_page = \
                        TopologicalPage(vertex, retina_drop_off_theshold,
                                        self._subgraph, self._placements,
                                        self._has_board, self._transciever)
                    #update tracker
                    self._vertex_mapper[vertex] = retina_page
        except ValueError:
            logger.info("entered text thats not convertable into a "
                        "integer, ignoring")
            pass

    def _remove_page(self, vertex):
        associated_page = self._vertex_mapper[vertex]
        del self._vertex_mapper[vertex]
        self._container.remove_page(associated_page.page)