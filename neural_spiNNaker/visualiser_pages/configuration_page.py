__author__ = 'stokesa6'
import gtk
from pyNN.visualiser_pages.raster_page import RasterPage
from pyNN.visualiser_pages.topological_page import TopologicalPage
import visualiser.visualiser_constants as visualiser_modes
from visualiser.abstract_page import AbstractPage
import logging
logger = logging.getLogger(__name__)


class ConfigPage(AbstractPage):

    RASTER_TEXT = "Raster_view"
    TOPOLOGICAL_TEXT = "Topological view"
    NOT_SET_TEXT = "Not set yet"
    INDIVIDUAL_RASTER_TEXT = "add as an individual raster plot"
    MERGED_RASTER_TEXT = "add to combination raster plot"

    def __init__(self,  vertex_mapper):
        AbstractPage.__init__(self)
        self.vertex_mapper = vertex_mapper
        self.drop_box_mapper = dict()
        self.raster_combo_box_selection = dict()
        self.main_combo_box_selection = dict()
        #set name of page
        self.config_page = gtk.Frame("population_config_page")

        #get vertexes which are set to record
        self.vertexes_in_question = list()
        for vertex in self.dao.vertices:
            if ((hasattr(vertex, 'is_set_to_record_spikes') and
               vertex.is_set_to_record_spikes)):
                self.vertexes_in_question.append(vertex)

        #set a table layout for the data
        self.table = gtk.Table(4, len(self.vertexes_in_question)+1, True)
        self.table.set_col_spacings(0)
        self.table.set_row_spacings(0)
        self.config_page.add(self.table)
        #add the vertex to the table
        self._add_vertexes()

        self.config_page.show_all()
        
    def is_page(self):
        return False

    def _add_vertexes(self):
        """
        goes though each vertex and adds its configurations options
        """
        #go though the vertexes and create a label and a dropbox box
        position = 0
        for vertex in self.vertexes_in_question:
            self.table.attach(gtk.Label(vertex.label), 0, 1,
                              position, position+1)
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
        self.table.attach(combo_box, 1, 2, position, position+1)
        #set active value to the one from defaults
        mode = vertex.visualiser_mode
        if mode == visualiser_modes.RASTER:
            self.main_combo_box_selection[position] = 0
            combo_box.set_active(0)
        elif mode == visualiser_modes.TOPOLOGICAL:
            combo_box.set_active(1)
            self.main_combo_box_selection[position] = 1
        else:
            self.main_combo_box_selection[position] = 2
            combo_box.set_active(2)
        return mode

    def _add_to_mapper(self, mappable_object, vertex, position, x):
        """updates the object tracker for removals and mapping to vertexes
        """
        self.drop_box_mapper[mappable_object] = dict()
        self.drop_box_mapper[mappable_object]['v'] = vertex
        self.drop_box_mapper[mappable_object]['p'] = position
        self.drop_box_mapper[mappable_object]['x'] = x

    def _changed_main_cb(self, combo_box):
        """handles the modification of the config table based on the
        choice made by the main entry combo box. This includes the removal of
        old entries in the table
        """
        model = combo_box.get_model()
        index = combo_box.get_active()
        data = self.drop_box_mapper[combo_box]
        if (index > -1 and
           (data['p'] not in self.main_combo_box_selection.keys() or
           index != self.main_combo_box_selection[data['p']])):

            self.main_combo_box_selection[data['p']] = index
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
                    self.table.remove(object_to_remove)
                    del self.drop_box_mapper[object_to_remove]
                self._add_to_mapper(text_box, data['v'], data['p'], data['x']+1)
                text_box.connect("activate", self._added_x_dimension)
                self.table.attach(text_box, data['x']+1, data['x']+2,
                                  data['p'], data['p']+1)
                text_box = gtk.Entry()
                if (data['v'].visualiser_2d_dimensions is not None and
                   data['v'].visualiser_2d_dimensions['y'] is not None):
                    text_box.set_text(str(data['v'].
                                      visualiser_2d_dimensions['y']))
                object_to_remove = self._locate_object(data['x']+2, data['p'])
                if object_to_remove is not None:
                    self.table.remove(object_to_remove)
                    del self.drop_box_mapper[object_to_remove]
                self._add_to_mapper(text_box, data['v'], data['p'], data['x']+2)
                text_box.connect("activate", self._added_y_dimension)
                self.table.attach(text_box, data['x']+2, data['x']+3,
                                  data['p'], data['p']+1)
            elif selected == self.RASTER_TEXT:
                data['v'].visualiser_2d_dimensions = {'x':None, 'y':None}
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
                    self.raster_combo_box_selection[data['p']] = 2
                    combo_box.set_active(2)
                elif raster_mode:
                    self.raster_combo_box_selection[data['p']] = 0
                    combo_box.set_active(0)
                else:
                    self.raster_combo_box_selection[data['p']] = 1
                    combo_box.set_active(1)

                object_to_remove = self._locate_object(data['x']+1, data['p'])
                if object_to_remove is not None:
                    self.table.remove(object_to_remove)
                    del self.drop_box_mapper[object_to_remove]
                self._add_to_mapper(combo_box, data['v'], data['p'], data['x']+1)
                self.table.attach(combo_box, data['x']+1, data['x']+2,
                                  data['p'], data['p']+1)
                combo_box.connect('changed', self._changed_raster_choice_cb)
                label = gtk.Label("")
                object_to_remove = self._locate_object(data['x']+2, data['p'])
                if object_to_remove is not None:
                    self.table.remove(object_to_remove)
                    del self.drop_box_mapper[object_to_remove]
                self._add_to_mapper(label, data['v'], data['p'], data['x']+2)
                self.table.attach(label, data['x']+2, data['x']+3, data['p'],
                                  data['p']+1)
            else:
                data['v'].visualiser_2d_dimensions = {'x': None, 'y': None}
                data['v'].visualiser_raster_seperate = None
                data['v'].visualiser_mode = None
                label = gtk.Label("")
                data['v'].visualiser_2d_dimensions = {'x': None, 'y': None}
                object_to_remove = self._locate_object(data['x']+1, data['p'])
                if object_to_remove is not None:
                    self.table.remove(object_to_remove)
                    del self.drop_box_mapper[object_to_remove]
                self._add_to_mapper(label, data['v'], data['p'], data['x']+1)
                self.table.attach(label, data['x']+1, data['x']+2, data['p'],
                                  data['p']+1)
                label = gtk.Label("")
                object_to_remove = self._locate_object(data['x']+2, data['p'])
                if object_to_remove is not None:
                    self.table.remove(object_to_remove)
                    del self.drop_box_mapper[object_to_remove]
                self._add_to_mapper(label, data['v'], data['p'], data['x']+2)
                self.table.attach(label, data['x']+2, data['x']+3, data['p'],
                                  data['p']+1)
            self.table.show_all()
            self._update_pages(selected, data['v'])

    def _update_pages(self, main_combo_selection, vertex):
        """
        updates all the pages so that they reflect decisions made by the config
        page
        """
        if ((main_combo_selection == self.NOT_SET_TEXT and
           vertex in self.vertex_mapper.keys())):
                self._remove_page(vertex)
        elif ((main_combo_selection == self.RASTER_TEXT and
              vertex in self.vertex_mapper.keys())):
                associated_page = self.vertex_mapper[vertex]
                if isinstance(associated_page, TopologicalPage):
                    self._remove_page(vertex)
        elif vertex in self.vertex_mapper.keys():  # topological position
            associated_page = self.vertex_mapper[vertex]
            if isinstance(associated_page, RasterPage):
                self.main_pages.remove(associated_page.page)

    def _locate_object(self, x, y):
        """
        locates an obhect given the x and y coords
        """
        for key in self.drop_box_mapper.keys():
            mappable_object = self.drop_box_mapper[key]
            if mappable_object['x'] == x and mappable_object['p'] == y:
                return key

    def _changed_raster_choice_cb(self, combo_box):
        """

        handle the changes made by the raster combo box, this includes
        making new pages and removing old pages as nessacry
        """
        model = combo_box.get_model()
        index = combo_box.get_active()
        data = self.drop_box_mapper[combo_box]
        if -1 < index != self.raster_combo_box_selection[data['p']]:
            selected = model[index][0]
            if selected == self.INDIVIDUAL_RASTER_TEXT:
                if data['v'] in self.vertex_mapper.keys():
                    associated_page = self.vertex_mapper[data['v']]
                    if (isinstance(associated_page, RasterPage)
                       and associated_page.is_merged_version):
                        self._remove_page(data['v'])
                        raster_page =\
                            RasterPage(vertex=data['v'], merged=False)
                        self.vertex_mapper[data['v']] = raster_page
                    else:
                        pass  # page already exists
                else:  # dont have a associated page
                    raster_page = RasterPage(vertex=data['v'], merged=False)
                    self.vertex_mapper[data['v']] = raster_page
            elif selected == self.MERGED_RASTER_TEXT:  # merged
                if data['v'] in self.vertex_mapper.keys():
                    associated_page = self.vertex_mapper[data['v']]
                    if (isinstance(associated_page, RasterPage)
                       and associated_page.is_merged_version):
                        pass  # already in merged page
                    elif isinstance(associated_page, RasterPage):
                        self._remove_page(data['v'])
                        located = False
                        for page in self.main_pages:
                            if (isinstance(page, RasterPage)
                               and page.is_merged_version):
                                page.add_vertex(data['v'])
                                self.vertex_mapper[data['v']] = page
                                located = True
                        if not located:
                            raster_page = RasterPage(vertex=data['v'],
                                                     merged=True)
                            self.vertex_mapper[data['v']] = raster_page
                else:  # no page set currently for the vertex,
                # locate any merged page and add it to it
                    found = False
                    for page in self.real_pages:
                        if (isinstance(page, RasterPage)
                           and page.is_merged_version):
                            found = True
                            page.add_vertex(data['v'])
                            self.vertex_mapper[data['v']] = page
                    if not found:  # no merged page found
                        raster_page = RasterPage(vertex=data['v'], merged=True)
                        self.vertex_mapper[data['v']] = raster_page
            else:  # not set
                if data['v'] in self.vertex_mapper.keys():
                    self._remove_page(data['v'])
        self.raster_combo_box_selection[data['p']] = index

    def _added_x_dimension(self, entry_box):
        """
        method that updates the x dimension of the vertex dimensions assuming
        its given valid input
        """
        text = entry_box.get_text()
        try:
            int_value = int(text)
            data = self.drop_box_mapper[entry_box]
            vertex = data['v']
            dimensions = vertex.visualiser_2d_dimensions
            vertex.visualiser_2d_dimensions = {'x': int_value,
                                               'y': dimensions['y']}
            #x isnt none otherwise we wouldnt have reached here
            if dimensions['y'] is not None:
                #already had a topological page
                if dimensions['x'] is not None:
                    self._remove_page(data['v'])
                    retina_page = TopologicalPage(vertex)
                    self.vertex_mapper[vertex] = retina_page
                else:
                    #create a topological view
                    retina_page = TopologicalPage(vertex)
                    #update tracker
                    self.vertex_mapper[vertex] = retina_page
        except ValueError:
            logger.info("entered text thats not "
                        "convertable into a integer, ignoring")
            pass

    def _added_y_dimension(self, entry_box):
        """
        method that updates the y dimension of the vertex dimensions assuming
        its given valid input
        """
        text = entry_box.get_text()
        try:
            int_value = int(text)
            data = self.drop_box_mapper[entry_box]
            vertex = data['v']
            dimensions = vertex.visualiser_2d_dimensions
            vertex.visualiser_2d_dimensions = {'y': int_value,
                                               'x': dimensions['x']}
             #x isnt none otherwise we wouldnt have reached here
            if dimensions['x'] is not None:
                #already had a topological page
                if dimensions['y'] is not None:
                    self._remove_page(data['v'])
                    retina_page = TopologicalPage(vertex)
                    self.vertex_mapper[vertex] = retina_page
                else:
                    #create a topological view
                    retina_page = TopologicalPage(vertex)
                    #update tracker
                    self.vertex_mapper[vertex] = retina_page
        except ValueError:
            logger.info("entered text thats not convertable into a "
                        "integer, ignoring")
            pass

    def _remove_page(self, vertex):
        associated_page = self.vertex_mapper[vertex]
        del self.vertex_mapper[vertex]
        self.main_pages.remove(associated_page.page)
        if vertex.visualiser_reset_counters:
            self.listener.remove_reset_call(associated_page)