from typing import List, Union

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, GLib, Gdk


class DataRow(Gtk.ListBoxRow):
    def __init__(self, main_window: 'FilenamesSelectorWindow',
                 file_index: int, filename: str):
        super(Gtk.ListBoxRow, self).__init__()

        self.filename = filename
        self.file_index = file_index
        self.main_window = main_window
        self.box = Gtk.Box(spacing=5)
        self.box.props.homogeneous = False

        filename_label = Gtk.Label(filename)
        filename_label.props.halign = Gtk.Align.START
        filename_label.props.hexpand = False
        filename_label.props.max_width_chars = 50
        filename_label.props.ellipsize = Pango.EllipsizeMode.END
        self.box.pack_start(filename_label, True, True, 0)

        play_button = Gtk.Button(label='Play')
        play_button.props.halign = Gtk.Align.END
        play_button.connect('clicked', self.on_button_click)
        self.box.pack_start(play_button, True, True, 0)

        self.add(self.box)

    def on_button_click(self, button):
        Gtk.main_quit()
        self.main_window.selected_file_index = self.file_index
        self.main_window.selected_file = self.filename
        self.main_window.destroy()


class FilenamesSelectorWindow(Gtk.Window):
    def __init__(self, filenames: List[List[Union[str, int]]]):
        Gtk.Window.__init__(self, title='Choose file to start playing', type_hint=Gdk.WindowTypeHint.DIALOG)
        self.set_border_width(5)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('delete-event', Gtk.main_quit)

        scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scroll.props.min_content_width = 400
        scroll.props.max_content_width = scroll.props.min_content_width
        scroll.props.max_content_height = 300
        scroll.props.propagate_natural_height = True
        self.add(scroll)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scroll.add(main_box)

        filenames_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        main_box.pack_start(filenames_list, True, True, 0)

        for filename, idx in sorted(filenames):
            filenames_list.add(DataRow(self, idx, filename))

        self.selected_file = None
        self.selected_file_index = None
        self.show_all()

    def open(self):
        Gtk.main()


if __name__ == '__main__':
    app = FilenamesSelectorWindow([['very ' + 'long ' * 50 + 'string to test', 0]] * 30)
    Gtk.main()
    print(app.selected_file)
