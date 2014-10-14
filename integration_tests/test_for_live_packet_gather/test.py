#!/usr/bin/env python
import gtk


class ComboBoxWrapExample:
    def __init__(self):
        self._data = None
        self.window = gtk.Window()
        self.window.connect('destroy', lambda w: gtk.main_quit())
        self.table = gtk.Table(4, 4, True)
        self.table.set_col_spacings(0)
        self.table.set_row_spacings(0)
        self.window.add(self.table)
        combobox = gtk.ComboBox()
        liststore = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell)
        combobox.add_attribute(cell, 'text', 0)
        self.table.attach(combobox, 1, 2, 0, 1)
        combobox.set_wrap_width(5)
        for n in range(50):
            liststore.append(['Item %d'%n])
        combobox.set_model(liststore)
        combobox.connect('changed', self.changed_cb)
        combobox.set_active(0)
        self.window.show_all()
        return

    def changed_cb(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index > -1:
            print model[index][0], 'selected'
            self._data = model[index][0]
            print self._data
        if index == 32:
            combobox = gtk.ComboBox()
            liststore = gtk.ListStore(str)
            cell = gtk.CellRendererText()
            combobox.pack_start(cell)
            combobox.add_attribute(cell, 'text', 0)
            self.table.attach(combobox, 2, 3, 0, 1)
            combobox.set_wrap_width(5)
            for n in range(50):
                liststore.append(['Item %d'%n])
            combobox.set_model(liststore)
            combobox.set_active(0)
            combobox.connect('changed', self.changed_cb2)
            self.window.show_all()
        return


    def changed_cb2(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index > -1:
            print model[index][0], 'selected'
        return
def main():
    gtk.main()
    return

if __name__ == "__main__":
    bcb = ComboBoxWrapExample()
    main()
