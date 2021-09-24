import tkinter as tk
import player
import queue
import sys
import os
import update_database as ud
import download_music as dm 
import pandas as pd
import ctypes
import webbrowser

from threading import Thread, Lock
from tkinter import messagebox
from tkinter import ttk 
from utils.top_level_locator import top_level_path
from pathlib import Path, PurePath
from random import sample
from shutil import copy

# s = ttk.Style()
# print(s.theme_names())
# print(s.theme_use())
# s.theme_use('clam')


# tell windows that python(w) is a host and not an application before it gets grouped as such
# therefore TASKBAR ICON will be set by tkinter now
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('arbitrary string')

# allows application to work without console in the background (pythonw.exe)
## it prevents print() and sys.stdout write calls which apparently block py2 and py3 in pyw mode 
if sys.executable.endswith("pythonw.exe"):
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.path.join(os.getenv("TEMP"), "stderr-"+os.path.basename(sys.argv[0])), "w")


class UserInterface(tk.Frame):
    OBJECTS = []
    RATING_DEFAULT = 75
    SOPHISTICATED_DEFAULT = 50
    MD = dm.MusicDownload()
    MDB = ud.MusicDatabase()
    JSON = MDB.load_database(MDB.database_path)
    RESOURCE_PATH = Path(top_level_path() / 'data' / 'resources' / 'icons')
    PLAYLIST_PATH = Path(top_level_path()) / 'data' / 'playlists'
    MUSIC_PATH =  Path(top_level_path()).parent / 'music'
    VOLUME = 0 # 0-100
    TIME = 0
    TIME_MEMORY = 0

    LABEL_COLOR = 'lightgreen'
    BACKGROUND_COLOR = 'black'
    ACCENT_COLOR = 'lightgreen'
    ACCENT_COLOR_SECONDARY = 'orange'

    def __init__(self, parent = None):
        tk.Frame.__init__(self, parent)
        UserInterface.OBJECTS.append(self)
        self.parent = parent
        self.pack(fill = 'both', expand = True)

        self.style_ttk_layout()
        self.initialize_global_layout()
        self.initialize_add_song_layout()
        self.initialize_songlist_layout()
        self.initialize_playlist_layout()
        self.initialize_playlist_list_layout()
        self.initialize_player_layout()

        self.queue = queue.Queue()
        self.initialize_playlists()
        self.after(1000, self.check_queue)
        

    def style_ttk_layout(self):
        self.style = ttk.Style()
        self.style.theme_create('style', parent='alt',
                        settings = {'TCombobox': {'configure': 
                                        {'selectbackground': self.BACKGROUND_COLOR,
                                        'fieldbackground': self.BACKGROUND_COLOR,
                                        'background': self.ACCENT_COLOR}},
                                    'TScrollbar': {'configure': 
                                        {'troughcolor': self.BACKGROUND_COLOR,
                                        'background': self.ACCENT_COLOR}},
                                    'Treeview': {'configure': 
                                        {'selectbackground': self.ACCENT_COLOR,
                                        'fieldbackground': self.BACKGROUND_COLOR,
                                        'background': self.BACKGROUND_COLOR}},
                                    'Treeview.Heading': {'configure': 
                                        {'foreground': self.LABEL_COLOR,
                                        'background': self.BACKGROUND_COLOR}},
                                    'TScale': {'configure':
                                        {'troughcolor': self.BACKGROUND_COLOR,
                                        'background': self.ACCENT_COLOR}},
                                    'TLabelframe': {'configure': 
                                        {'background': self.BACKGROUND_COLOR,
                                        'relief': 'solid', # DEVNOTE: has to be 'solid' to color 
                                        'bordercolor': self.ACCENT_COLOR_SECONDARY,
                                        'borderwidth': 1}},
                                    'TLabelframe.Label': {'configure': 
                                        {'foreground': self.LABEL_COLOR,
                                        'background': self.BACKGROUND_COLOR}}})
        self.style.theme_use('style')

        
    def recolor_trees(self):
        self.playlist_tree.tag_configure(self.LABEL_COLOR, foreground=self.LABEL_COLOR) 
        self.playlist_tree.tag_configure(self.ACCENT_COLOR_SECONDARY, foreground=self.ACCENT_COLOR_SECONDARY)

    def initialize_playlists(self, path = None):
        # empty playlist
        self.remove_all_songs_from_playlist()

        if path == None:
            # get json playlists from playlist folder 
            files = []
            files.extend(self.PLAYLIST_PATH.glob('**/*.json'))
            # select topmost playlist from list
            playlist_file = files[0]
        else:
            playlist_file = path
        # load df from json playlist
        playlist_df = self.MDB.load_database(playlist_file)
        # use indices from df as IID for treeview and populate the playlist_treeview
        for index in playlist_df.iids:
            values = self.tree.item(index)['values']
            try:
                self.playlist_tree.insert(parent = '', index = 'end', iid = index, text = index, values = values, tags = self.tree.item(index)['tags'])
            except tk.TclError as e:
                self.playlist_lf.config(text = "Playlist: cannot add duplicates", fg = 'red')

        self.recolor_trees()

        self.playlist_lf.config(text = f"Playlist {Path(playlist_file).stem} initialized", fg = 'green')

        if path == None:
            # set playlists tree
            for index, filepath in enumerate(files):
                color = self.LABEL_COLOR
                playlist_name = Path(filepath).stem
                self.playlist_list_tree.insert(parent = '', index = 'end', iid = filepath, text = filepath, tags = (color,), values = playlist_name)
            self.playlist_list_tree.tag_configure(self.LABEL_COLOR, foreground=self.LABEL_COLOR) 

        # set GUI values on initialize
        self.on_single_click_either_tree(iid = playlist_df.iids[0])

        filepath = self.JSON.loc[playlist_df.index[0]]['filepath']
        self.set_song_end_time(self.JSON.loc[playlist_df.iids[0]]['duration']) 
        if path == None:
            def run_player():
                player.Player(play_volume = self.VOLUME/100, song_index = 0, queue = self.queue, filepath = filepath)
            music_player_T = Thread(target=run_player, daemon = True)
            music_player_T.start()
        else:
            self.reset_song(iid = playlist_df.iids[0])
     

    def initialize_global_layout(self):
        self.add_song_lf_l = ttk.Label(text = "Youtube-DL: Adjust metadata for filtering!") # TODO see next todo and fix that everywhere needed 
        self.add_song_lf = ttk.LabelFrame(self, labelwidget = self.add_song_lf_l)
        self.songlist_lf = ttk.LabelFrame(self, text = "Songlist")
        self.playlist_lf = tk.LabelFrame(self, text = "Playlist", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.player_playlist_lf = ttk.LabelFrame(self, text = "Player & Playlists")
        self.player_f = tk.Frame(self.player_playlist_lf, bg = self.BACKGROUND_COLOR)
        self.playlist_list_f = tk.Frame(self.player_playlist_lf, bg = self.BACKGROUND_COLOR)
        
        self.add_song_lf.grid(row = 0, column = 0, rowspan = 3, columnspan = 1, sticky=tk.NSEW)
        self.songlist_lf.grid(row = 0, column = 2, rowspan = 3, columnspan = 1, sticky=tk.NSEW)
        self.playlist_lf.grid(row = 3, column = 2, rowspan = 3, columnspan = 1, sticky=tk.NSEW)
        self.player_playlist_lf.grid(row = 3, column = 0, rowspan = 3, columnspan = 1, sticky=tk.NSEW)
        self.player_f.grid(row = 0, column = 0, rowspan = 3, columnspan = 1)
        self.playlist_list_f.grid(row = 0, column = 2, rowspan = 3, columnspan = 1, sticky=tk.E)

        
    def initialize_player_layout(self):
        # set images
        self.player_play_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'play.png'), name='test', master=self)
        self.player_pause_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'pause.png'), master=self)
        self.player_mute_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'mute.png'), master=self)
        self.player_sound_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'sound.png'), master=self)
        self.player_sound_low_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'sound low.png'), master=self)
        self.player_sound_lowest_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'sound lowest.png'), master=self)
        self.player_shuffle_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'shuffle.png'), master=self)
        self.player_previous_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'previous.png'), master=self)
        self.player_next_img = tk.PhotoImage(file=Path(self.RESOURCE_PATH / 'next.png'), master=self)
        
        # resize images
        # self.player_stop_img = self.player_stop_img.subsample(6, 6)
        self.player_play_img = self.player_play_img.subsample(6, 6)
        self.player_pause_img = self.player_pause_img.subsample(6, 6)
        self.player_mute_img = self.player_mute_img.subsample(6, 6)
        self.player_sound_img = self.player_sound_img.subsample(6, 6)
        self.player_sound_low_img = self.player_sound_low_img.subsample(6, 6)
        self.player_sound_lowest_img = self.player_sound_lowest_img.subsample(6, 6)
        self.player_shuffle_img = self.player_shuffle_img.subsample(6, 6)
        self.player_previous_img = self.player_previous_img.subsample(6, 6)
        self.player_next_img = self.player_next_img.subsample(6, 6)

            
        self.player_song_bar_function = tk.Frame(self.player_f, bg = self.BACKGROUND_COLOR)
        self.player_song_function_f = tk.Frame(self.player_f, bg = self.BACKGROUND_COLOR)
        self.player_volume_f = tk.Frame(self.player_f, bg = self.BACKGROUND_COLOR)

        self.player_progress_start_l = tk.Label(self.player_song_bar_function, text = '00:00', bg = self.BACKGROUND_COLOR, fg = self.LABEL_COLOR)
        self.player_progress_end_l = tk.Label(self.player_song_bar_function, text = '99:99', bg = self.BACKGROUND_COLOR, fg = self.LABEL_COLOR)

        class Scale(ttk.Scale):
            """a type of Scale where the left click is hijacked to work like a right click"""
            def __init__(self, master=None, **kwargs):
                ttk.Scale.__init__(self, master, **kwargs)
                self.bind('<Button-1>', self.set_scale_value_fast)
            def set_scale_value_fast(self, event):
                self.event_generate('<Button-3>', x=event.x, y=event.y)
                return 'break'
        self.player_progress_s = Scale(self.player_song_bar_function, from_ = 0, to = 100, orient=tk.HORIZONTAL, value = 0, command=self.set_song_progression, length = 300)
        self.player_volume_s = Scale(self.player_volume_f, from_ = 0, to = 100, orient=tk.HORIZONTAL, value = self.VOLUME, command=self.slide_volume, length = 300)
    


        # set images on buttons
        # self.player_stop_btn = tk.Button(self.player_song_function_f, image = self.player_stop_img, borderwidth = 0, width=115)
        self.player_playpause_btn = tk.Button(self.player_song_function_f, text='play', image = self.player_pause_img, borderwidth = 0, width=115, command=self.playpause_song, bg = self.BACKGROUND_COLOR)
        self.player_sound_btn = tk.Button(self.player_volume_f, borderwidth = 0, width=115, command = self.mute_unmute, bg = self.BACKGROUND_COLOR)
        self.set_volume_icon(self.VOLUME)
        self.player_shuffle_btn = tk.Button(self.player_volume_f, image = self.player_shuffle_img, borderwidth = 0, width=115, command = self.shuffle_playlist, bg = self.BACKGROUND_COLOR)
        self.player_previous_btn = tk.Button(self.player_song_function_f, image = self.player_previous_img, borderwidth = 0, width=115, command = self.set_previous_song, bg = self.BACKGROUND_COLOR)
        self.player_next_btn = tk.Button(self.player_song_function_f, image = self.player_next_img, borderwidth = 0, width=115, command = self.set_next_song, bg = self.BACKGROUND_COLOR)


        # pack image buttons
        self.player_volume_f.pack() # .grid(row=0, column=0, rowspan=1, columnspan = 5)
        self.player_song_function_f.pack() # .grid(row=1, column=0, rowspan=1, columnspan = 5)
        self.player_song_bar_function.pack(fill = 'both', expand=True) # .grid(row=2, column=0, rowspan=1, columnspan = 7)

        self.player_previous_btn.pack(side=tk.LEFT)
        self.player_playpause_btn.pack(side=tk.LEFT)
        self.player_next_btn.pack(side=tk.LEFT)
        
        self.player_sound_btn.pack(side=tk.LEFT)
        self.player_volume_s.pack(side=tk.LEFT)
        self.player_shuffle_btn.pack(side=tk.LEFT)

        self.player_progress_start_l.pack(side=tk.LEFT)
        self.player_progress_s.pack(side=tk.LEFT, fill = 'both', expand=True)
        self.player_progress_end_l.pack(side=tk.LEFT)


    def on_double_click_playlist_list_tree(self, event):
        if len(self.playlist_list_tree.selection()) == 1:
            path = self.playlist_list_tree.selection()[0]
            self.initialize_playlists(path = path)
            
        
    def initialize_playlist_list_layout(self):
        self.playlist_list_top_frame = tk.Frame(self.playlist_list_f)
        self.playlist_list_bottom_frame = tk.Frame(self.playlist_list_f)
        
        # tree view scrollbar
        self.playlist_list_tree_scroll_y = ttk.Scrollbar(self.playlist_list_bottom_frame)

        self.playlist_list_tree = ttk.Treeview(self.playlist_list_bottom_frame, height = 13, yscrollcommand = self.playlist_list_tree_scroll_y.set)
        self.playlist_list_tree.bind('<Double-Button-1>', self.on_double_click_playlist_list_tree)
        self.playlist_list_tree_detached = []

        self.playlist_list_tree['columns'] = ('Playlists')
        self.playlist_list_tree.column('#0', width = 0, stretch = tk.NO)
        self.playlist_list_tree.column('Playlists', width = 200)
        def treeview_sort_column(tv, col, reverse):
            column_index = self.playlist_list_tree["columns"].index(col)
            l = [(str(tv.item(k)["values"][column_index]), k) for k in tv.get_children()]
            l.sort(key=lambda t: t[0], reverse=reverse)
            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)
            tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))
        self.playlist_list_tree.heading('#0', text = '', command=lambda : treeview_sort_column(self.playlist_list_tree, "#0", False))
        self.playlist_list_tree.heading('Playlists', text = 'Playlists', command=lambda : treeview_sort_column(self.playlist_list_tree, "Playlists", False))
        self.tree.heading('Album', text = 'Album', command=lambda : treeview_sort_column(self.tree, "Album", False))

        self.playlist_list_delete_b = tk.Button(self.playlist_list_top_frame, text = 'Delete', command = self.delete_playlists, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.playlist_list_search_str = tk.StringVar()
        self.playlist_list_search_str.trace('w', lambda name, index, mode, sv=self.playlist_list_search_str: self.search_playlist_list(sv))
        self.playlist_list_search_e = tk.Entry(self.playlist_list_top_frame, textvariable = self.playlist_list_search_str, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR)



        # pack and configure to frame 
        self.playlist_list_top_frame.pack(side = tk.TOP, fill="both", expand=True)
        self.playlist_list_bottom_frame.pack(side = tk.TOP, fill="both", expand=True)

        self.playlist_list_delete_b.pack(side=tk.LEFT, fill = 'both', expand = True)
        self.playlist_list_search_e.pack(side=tk.RIGHT, fill = 'both', expand = True)

        self.playlist_list_tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_list_tree_scroll_y.config(command=self.playlist_list_tree.yview)
        self.playlist_list_tree.pack(side=tk.BOTTOM, fill = 'both', expand = True)

    def delete_playlists(self):
        selection = self.playlist_list_tree.selection()
        for playlist in selection:
            Path(playlist).unlink()
            self.playlist_list_tree.delete(playlist)


    def search_playlist_list(self, event = None):
        all_children = list(self.playlist_list_tree.get_children()) + self.playlist_list_tree_detached
        self.playlist_list_tree_detached.clear()
        search = self.playlist_list_search_e.get()
        search = search.strip(' ')

        for playlist in all_children:
            # if query in name 
            if search.lower() in playlist.split('\\')[-1][:-5].lower():
                self.playlist_list_tree.reattach(playlist, '', 'end')
            else:
                self.playlist_list_tree_detached.append(playlist)
                self.playlist_list_tree.detach(playlist)

    
    def search_playlist(self, event = None):
        all_children = list(self.playlist_tree.get_children()) + list(self.playlist_tree_detached)
        self.playlist_tree_detached.clear()
        search = self.save_songs_to_playlist_e.get()
        search = search.strip(' ')

        for iid in all_children:
            iid = int(iid)
            query_string = self.get_query_information(iid = iid)
            # if query in name 
            if search.lower() in query_string.lower():
                self.playlist_tree.reattach(str(iid), '', 'end')
            else:
                self.playlist_tree_detached.add(str(iid))
                self.playlist_tree.detach(str(iid))


    def get_query_information(self, iid):
        db = self.JSON.loc[iid]
        string = ''
        for value in db['artist']:
            string += f'{value} '
        string += f"{db['song']} "
        string += f"{db['album']} "
        return string


    def initialize_playlist_layout(self):
        self.playlist_top_frame = tk.Frame(self.playlist_lf)
        self.playlist_bottom_frame = tk.Frame(self.playlist_lf)
        
        self.add_all_songs_to_playlist_b = tk.Button(self.playlist_top_frame, text = 'Add all', command = self.add_all_songs_to_playlist, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.add_songs_to_playlist_b = tk.Button(self.playlist_top_frame, text = 'Add', command = self.add_songs_to_playlist, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.remove_all_songs_to_playlist_b = tk.Button(self.playlist_top_frame, text = 'Remove all', command = self.remove_all_songs_from_playlist, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.remove_songs_to_playlist_b = tk.Button(self.playlist_top_frame, text = 'Remove', command = self.remove_songs_from_playlist, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.save_songs_to_car_playlist_b = tk.Button(self.playlist_top_frame, text = 'Car save', command = self.save_mp3s_to_car_playlist_folder, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        # self.save_songs_to_playlist_b = tk.Button(self.playlist_top_frame, text = 'Save', command = self.save_songs_from_playlist, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)

        self.save_songs_to_playlist_e_str = tk.StringVar()
        self.save_songs_to_playlist_e_str.trace('w', lambda name, index, mode, sv=self.save_songs_to_playlist_e_str: self.search_playlist(sv))
        self.save_songs_to_playlist_e = tk.Entry(self.playlist_top_frame, textvariable = self.save_songs_to_playlist_e_str, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR)
        self.save_songs_to_playlist_e.bind('<Return>', self.save_songs_from_playlist)

        

        # tree view scrollbar
        self.playlist_tree_scroll_y = ttk.Scrollbar(self.playlist_bottom_frame)

        # tree with columns, headers, and header sorting
        self.playlist_tree = ttk.Treeview(self.playlist_bottom_frame, height = 13, yscrollcommand = self.playlist_tree_scroll_y.set)
        self.playlist_tree_detached = set()
        self.playlist_tree.bind('<ButtonRelease-1>', self.on_single_click_playlist_tree)
        self.playlist_tree.bind("<Double-Button-1>", self.on_double_click_playlist_tree)
        self.playlist_tree['columns'] = ('Artist', 'Song', '*', 'Genre', 'Emotion', 'Date', 'Language', 'Vocal', 'Instrument', 'Album')
        self.playlist_tree.column('#0', width = 0, stretch = tk.NO)
        self.playlist_tree.column('Artist', width = 165)
        self.playlist_tree.column('Song', width = 290)
        self.playlist_tree.column('*', width = 20)
        self.playlist_tree.column('Genre', width = 105)
        self.playlist_tree.column('Emotion', width = 100)
        self.playlist_tree.column('Date', width = 60)
        self.playlist_tree.column('Language', width = 60)
        self.playlist_tree.column('Vocal', width = 55)
        self.playlist_tree.column('Instrument', width = 75)
        self.playlist_tree.column('Album', width = 145)
        def treeview_sort_column(tv, col, reverse):
            column_index = self.tree["columns"].index(col)
            l = [(str(tv.item(k)["values"][column_index]), k) for k in tv.get_children()]
            l.sort(key=lambda t: t[0], reverse=reverse)
            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)
            tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))
        self.playlist_tree.heading('#0', text = '', command=lambda : treeview_sort_column(self.playlist_tree, "#0", False))
        self.playlist_tree.heading("Artist", text = 'Artist', command=lambda : treeview_sort_column(self.playlist_tree, "Artist", False))
        self.playlist_tree.heading('Song', text = 'Song', command=lambda : treeview_sort_column(self.playlist_tree, "Song", False))
        self.playlist_tree.heading('*', text = '*', command=lambda : treeview_sort_column(self.playlist_tree, "*", False))
        self.playlist_tree.heading('Genre', text = 'Genre', command=lambda : treeview_sort_column(self.playlist_tree, "Genre", False))
        self.playlist_tree.heading('Emotion', text = 'Emotion', command=lambda : treeview_sort_column(self.playlist_tree, "Emotion", False))
        self.playlist_tree.heading('Date', text = 'Date', command=lambda : treeview_sort_column(self.playlist_tree, "Date", False))
        self.playlist_tree.heading('Language', text = 'Language', command=lambda : treeview_sort_column(self.playlist_tree, "Language", False))
        self.playlist_tree.heading('Vocal', text = 'Vocal', command=lambda : treeview_sort_column(self.playlist_tree, "Vocal", False))
        self.playlist_tree.heading('Instrument', text = 'Instrument', command=lambda : treeview_sort_column(self.playlist_tree, "Instrument", False))
        self.playlist_tree.heading('Album', text = 'Album', command=lambda : treeview_sort_column(self.playlist_tree, "Album", False))
       

        # pack and configure to frame 
        self.playlist_top_frame.pack(side = tk.TOP, fill="both", expand=True)
        self.playlist_bottom_frame.pack(side = tk.BOTTOM, fill="both", expand=True)
       
        self.add_all_songs_to_playlist_b.pack(side=tk.LEFT, fill = 'both', expand = True)
        self.add_songs_to_playlist_b.pack(side=tk.LEFT, fill = 'both', expand = True)
        self.remove_all_songs_to_playlist_b.pack(side=tk.LEFT, fill = 'both', expand = True)
        self.remove_songs_to_playlist_b.pack(side=tk.LEFT, fill = 'both', expand = True)
        self.save_songs_to_car_playlist_b.pack(side=tk.LEFT, fill = 'both', expand = True)
        # self.save_songs_to_playlist_b.pack(side=tk.LEFT, fill = 'both', expand = True)
        self.save_songs_to_playlist_e.pack(side=tk.LEFT, fill = 'both', expand = True)

        self.playlist_tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_tree_scroll_y.config(command=self.playlist_tree.yview)
        self.playlist_tree.pack(side=tk.BOTTOM)


    def initialize_songlist_layout(self):
        # tree view scrollbar
        self.tree_scroll_y = ttk.Scrollbar(self.songlist_lf)

        # tree with columns, headers, and header sorting
        self.tree = ttk.Treeview(self.songlist_lf, height = 13, yscrollcommand = self.tree_scroll_y.set)
        self.tree_detached = set()
        self.tree.bind('<ButtonRelease-1>', self.on_single_click_songlist_tree)
        self.tree.bind("<Double-Button-1>", self.on_double_click_songlist_tree)
        self.tree['columns'] = ('Artist', 'Song', '*', 'Genre', 'Emotion', 'Date', 'Language', 'Vocal', 'Instrument', 'Album')
        self.tree.column('#0', width = 0, stretch = tk.NO)
        self.tree.column('Artist', width = 165)
        self.tree.column('Song', width = 290)
        self.tree.column('*', width = 20)
        self.tree.column('Genre', width = 105)
        self.tree.column('Emotion', width = 100)
        self.tree.column('Date', width = 60)
        self.tree.column('Language', width = 60)
        self.tree.column('Vocal', width = 55)
        self.tree.column('Instrument', width = 75)
        self.tree.column('Album', width = 145)
        def treeview_sort_column(tv, col, reverse):
            column_index = self.tree["columns"].index(col)
            l = [(str(tv.item(k)["values"][column_index]), k) for k in tv.get_children()]
            l.sort(key=lambda t: t[0], reverse=reverse)
            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)
            tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))
        self.tree.heading('#0', text = '', command=lambda : treeview_sort_column(self.tree, "#0", False))
        self.tree.heading("Artist", text = 'Artist', command=lambda : treeview_sort_column(self.tree, "Artist", False))
        self.tree.heading('Song', text = 'Song', command=lambda : treeview_sort_column(self.tree, "Song", False))
        self.tree.heading('*', text = '*', command=lambda : treeview_sort_column(self.tree, "*", False))
        self.tree.heading('Genre', text = 'Genre', command=lambda : treeview_sort_column(self.tree, "Genre", False))
        self.tree.heading('Emotion', text = 'Emotion', command=lambda : treeview_sort_column(self.tree, "Emotion", False))
        self.tree.heading('Date', text = 'Date', command=lambda : treeview_sort_column(self.tree, "Date", False))
        self.tree.heading('Language', text = 'Language', command=lambda : treeview_sort_column(self.tree, "Language", False))
        self.tree.heading('Vocal', text = 'Vocal', command=lambda : treeview_sort_column(self.tree, "Vocal", False))
        self.tree.heading('Instrument', text = 'Instrument', command=lambda : treeview_sort_column(self.tree, "Instrument", False))
        self.tree.heading('Album', text = 'Album', command=lambda : treeview_sort_column(self.tree, "Album", False))

        # load up data from global
        for index, row in self.JSON.iterrows():
            genre = row['genre'][0] if row['genre'] != [] else ""
            emotion = row['emotion'][0] if row['emotion'] != [] else ""
            vocal = row['vocal'][0] if row['vocal'] != [] else ""
            instrument = row['instrument'][0] if row['instrument'] != [] else ""

            color = self.ACCENT_COLOR_SECONDARY if row['downloaded'] == 0 else self.LABEL_COLOR 

            self.tree.insert(parent = '', index = 'end', iid = index, text = index, tags = (color,), values = (
                row['artist'][0], row['song'], row['rating'], genre, emotion, row['year_added'], row['language'], vocal, instrument, row['album']))
        self.tree.tag_configure(self.LABEL_COLOR, foreground=self.LABEL_COLOR) 
        self.tree.tag_configure(self.ACCENT_COLOR_SECONDARY, foreground=self.ACCENT_COLOR_SECONDARY) 
        
        # pack and configure to frame 
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree.pack()


    def initialize_add_song_layout(self):
        self.add_song_listbox_height = 12

        self.link_l = tk.Label(self.add_song_lf, text = "Link", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.link_e = tk.Entry(self.add_song_lf, state = 'disabled', fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR, disabledforeground = self.LABEL_COLOR, disabledbackground = self.BACKGROUND_COLOR)
        self.link_l.bind('<Button-1>', self.go_to_youtube)
        self.link_e.bind('<Button-1>', self.go_to_youtube)

        try:
            print("clipboard:", self.clipboard_get())
        except:
            pass
        
        self.song_l = tk.Label(self.add_song_lf, text = "Song", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR) 
        self.song_e = tk.Entry(self.add_song_lf, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR)
        self.song_l.bind('<Button-1>', self.switch_song_artists)
        self.artist_l = tk.Label(self.add_song_lf, text = "Artist(s)", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.artist_e = tk.Entry(self.add_song_lf, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR)
        self.artist_l.bind('<Button-1>', self.switch_song_artists)
        self.genre_l = tk.Label(self.add_song_lf, text = "Genre(s)", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.genre_f = tk.Frame(self.add_song_lf)
        self.genre_f.grid(row = 8, column = 1, sticky = 'w')
        self.genre_sb = ttk.Scrollbar(self.genre_f)
        self.genre_sb.pack(side = 'right', fill = 'y')
        self.genre_lb = tk.Listbox(self.genre_f, exportselection = 0, height = self.add_song_listbox_height, width = 15, yscrollcommand = self.genre_sb.set, selectmode = "multiple", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.genre_values = sorted(["Electric", "Jazz", "Comedy", "Pop", "Singer songwriter", "Rock", "Metal", "Soul", "House", "Vocal", "Rap", "Country", "Big Band", "Trippy", "Art", "Funk"])
        for i in range(0, len(self.genre_values)):
            self.genre_lb.insert(i, self.genre_values[i])
            self.genre_lb.itemconfig(i, selectbackground = self.ACCENT_COLOR)
        self.genre_lb.pack(side = 'left')
        self.genre_sb.config(command = self.genre_lb.yview)
        self.genre_lb.bind("<Button-1>", self.set_antifilter_color)
        self.genre_lb.bind("<Button-3>", self.set_antifilter_color)
        
        self.album_l = tk.Label(self.add_song_lf, text = "Album", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.album_e = tk.Entry(self.add_song_lf, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR)
        self.type_l = tk.Label(self.add_song_lf, text = "Type", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.type_sv = tk.StringVar()
        self.type_values = ["", "Single", "EP", "Cover", "Remix", "Mashup"]
        self.type_cb = ttk.Combobox(self.add_song_lf, textvariable = self.type_sv, state = 'readonly', values = self.type_values, foreground = self.LABEL_COLOR)
        self.type_cb.current(0)
        self.release_year_l = tk.Label(self.add_song_lf, text = "Release year", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.release_year_e = tk.Entry(self.add_song_lf, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR)
        self.clear_b = tk.Button(self.add_song_lf, text = 'Clear', command = self.clear_filter_entries, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.filter_b = tk.Button(self.add_song_lf, text = 'Filter', command = self.filter_using_entries, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.duration_l = tk.Label(self.add_song_lf, text = "Duration (s)", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.duration_e = tk.Entry(self.add_song_lf, state = 'disabled', fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR, disabledforeground = self.LABEL_COLOR, disabledbackground = self.BACKGROUND_COLOR)
        self.rating_l = tk.Label(self.add_song_lf, text = f"Rating: {self.RATING_DEFAULT}", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.rating_s = ttk.Scale(self.add_song_lf, from_ = 0, to = 100, command = self.update_rating, orient = 'horizontal') # resolution = 1, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR
        self.rating_s.set(self.RATING_DEFAULT)
        
        self.sophisticated_l = tk.Label(self.add_song_lf, text = f"Sophisticated: {self.SOPHISTICATED_DEFAULT}", width = 14, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.sophisticated_s = ttk.Scale(self.add_song_lf, from_ = 0, to = 100, command = self.update_sophisticated, orient = 'horizontal')
        self.sophisticated_s.set(self.SOPHISTICATED_DEFAULT)

        self.emotion_l = tk.Label(self.add_song_lf, text = "Emotion(s)", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.emotion_f = tk.Frame(self.add_song_lf)
        self.emotion_f.grid(row = 8, column = 3, sticky = 'w')
        self.emotion_sb = ttk.Scrollbar(self.emotion_f)
        self.emotion_sb.pack(side = 'right', fill = 'y')
        self.emotion_lb = tk.Listbox(self.emotion_f, exportselection=0, height = self.add_song_listbox_height, width = 15, yscrollcommand = self.emotion_sb.set, selectmode = "multiple", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.emotion_values = sorted(["Happy", "Sad", "Love", "Chill", "Chaos", "Gaming", "Focus", "Visualization", "Nostalgia", "Meditation", "Sport"])
        for i in range(0, len(self.emotion_values)):
            self.emotion_lb.insert(i, self.emotion_values[i])
            self.emotion_lb.itemconfig(i, selectbackground = self.ACCENT_COLOR)
        self.emotion_lb.pack(side = 'left')
        self.emotion_sb.config(command = self.emotion_lb.yview)
        self.emotion_lb.bind("<Button-1>", self.set_antifilter_color)
        self.emotion_lb.bind("<Button-3>", self.set_antifilter_color)

        self.instrument_l = tk.Label(self.add_song_lf, text = "Instrument(s)", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.instrument_f = tk.Frame(self.add_song_lf)
        self.instrument_f.grid(row = 8, column = 5, sticky = 'w')
        self.instrument_sb = ttk.Scrollbar(self.instrument_f)
        self.instrument_sb.pack(side = 'right', fill = 'y')
        self.instrument_lb = tk.Listbox(self.instrument_f, exportselection=0, height = self.add_song_listbox_height, width = 15, yscrollcommand = self.instrument_sb.set, selectmode = "multiple", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.instrument_values = sorted(["Guitar", "Piano", 'Flute', 'Drum', 'Harmonica', 'Saxophone', 'Trumpet', 'Violin', 'Bass'])
        for i in range(0, len(self.instrument_values)):
            self.instrument_lb.insert(i, self.instrument_values[i])
            self.instrument_lb.itemconfig(i, selectbackground = self.ACCENT_COLOR)
        self.instrument_lb.pack(side = 'left')
        self.instrument_sb.config(command = self.instrument_lb.yview)
        self.instrument_lb.bind("<Button-1>", self.set_antifilter_color)
        self.instrument_lb.bind("<Button-3>", self.set_antifilter_color)

        self.vocal_l = tk.Label(self.add_song_lf, text = "Vocal(s)", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.vocal_f = tk.Frame(self.add_song_lf)
        self.vocal_f.grid(row = 8, column = 7, sticky = 'w')
        self.vocal_sb = ttk.Scrollbar(self.vocal_f)
        self.vocal_sb.pack(side = 'right', fill = 'y')
        self.vocal_lb = tk.Listbox(self.vocal_f, exportselection=0, height = self.add_song_listbox_height, width = 15, yscrollcommand = self.vocal_sb.set, selectmode = "multiple", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.vocal_values = ["Female", "Male", "Duo", "Trio", "Quartet", "Barbershop", "Multiple", "Acapella"]
        for i in range(0, len(self.vocal_values)):
            self.vocal_lb.insert(i, self.vocal_values[i])
            self.vocal_lb.itemconfig(i, selectbackground = self.ACCENT_COLOR)
        self.vocal_lb.pack(side = 'left')
        self.vocal_sb.config(command = self.vocal_lb.yview)
        self.vocal_lb.bind("<<ListboxSelect>>", self.set_vocal_default)
        self.vocal_lb.bind("<Button-1>", self.set_antifilter_color)
        self.vocal_lb.bind("<Button-3>", self.set_antifilter_color)

        self.language_l = tk.Label(self.add_song_lf, text = "Language", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.language_values = ["", "English", "Dutch", "French", "German", "Asian"]
        self.language_cb = ttk.Combobox(self.add_song_lf, state = 'readonly', values = self.language_values, foreground = self.LABEL_COLOR)
        self.language_cb.current(0)
        self.year_added_l = tk.Label(self.add_song_lf, text = "Year added", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)
        self.year_added_e = tk.Entry(self.add_song_lf, state = 'disabled', fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR, insertbackground = self.LABEL_COLOR, disabledforeground = self.LABEL_COLOR, disabledbackground = self.BACKGROUND_COLOR)
        
        self.add_database_b = tk.Button(self.add_song_lf, text = "Update database", command = self.add_song_to_database, fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)

        self.song_l.grid(row = 0, column = 0, sticky = 'e')
        self.song_e.grid(row = 0, column = 1, sticky = 'w')
        self.artist_l.grid(row = 1, column = 0, sticky = 'e')
        self.artist_e.grid(row = 1, column = 1, sticky = 'w')
        self.album_l.grid(row = 2, column = 0, sticky = 'e')
        self.album_e.grid(row = 2, column = 1, sticky = 'w')
        self.release_year_l.grid(row = 3, column = 0, sticky = 'e')
        self.release_year_e.grid(row = 3, column = 1, sticky = 'w')
        self.rating_l.grid(row = 0, column = 2, rowspan = 2, sticky = 'e')
        self.rating_s.grid(row = 0, column = 3, rowspan = 2, sticky = 'w')
        self.sophisticated_l.grid(row = 2, column = 2, rowspan = 2, sticky = 'e')
        self.sophisticated_s.grid(row = 2, column = 3, rowspan = 2, sticky = 'w')
        
        self.genre_l.grid(row = 8, column = 0, sticky = 'e')
        self.emotion_l.grid(row = 8, column = 2, sticky = 'e')

        self.type_l.grid(row = 2, column = 6, sticky = 'e')
        self.type_cb.grid(row = 2, column = 7, sticky = 'w')
        self.vocal_l.grid(row = 8, column = 6, sticky = 'e')
        self.language_l.grid(row = 3, column = 6, sticky = 'e')
        self.language_cb.grid(row = 3, column = 7, sticky = 'w')
        self.link_l.grid(row = 3, column = 4, sticky = 'e')
        self.link_e.grid(row = 3, column = 5, sticky = 'w')
        
        self.clear_b.grid(row = 0, column = 4, sticky = 'e')
        self.filter_b.grid(row = 0, column = 5, sticky = 'w')
        self.duration_l.grid(row = 1, column = 4, sticky = 'e')
        self.duration_e.grid(row = 1, column = 5, sticky = 'w')
        self.year_added_l.grid(row = 2, column = 4, sticky = 'e')
        self.year_added_e.grid(row = 2, column = 5, sticky = 'w')
        self.instrument_l.grid(row = 8, column = 4, sticky = 'e')

        self.add_database_b.grid(row = 0, column = 7)


    def switch_song_artists(self, *args):
        artists = self.song_e.get()
        song = self.artist_e.get()
        self.song_e.delete(0, tk.END)
        self.artist_e.delete(0, tk.END)
        self.song_e.insert(0, song)
        self.artist_e.insert(0, artists)

    
    def go_to_youtube(self, event):
        url = self.link_e.get()
        chrome_path = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
        if 'youtube' in url:
            webbrowser.get(chrome_path).open(url)
            self.pause_song()


    def set_antifilter_color(self, event):
        iid = self.vocal_lb.nearest(y = event.y)
        # left click
        if event.num == 1:
            event.widget.itemconfig(iid, selectbackground = self.ACCENT_COLOR)
        # right click 
        if event.num == 3:
            if event.widget.itemcget(index = iid, option = 'selectbackground') == self.ACCENT_COLOR:
                event.widget.itemconfig(iid, selectbackground = self.ACCENT_COLOR_SECONDARY)
                event.widget.selection_set(iid)
            elif event.widget.itemcget(index = iid, option = 'selectbackground') == self.ACCENT_COLOR_SECONDARY:
                event.widget.itemconfig(iid, selectbackground = self.ACCENT_COLOR)
                event.widget.selection_clear(iid)
        
        
    def set_vocal_default(self, event, *args):
        if self.language_cb.get() == '':
            self.language_cb.current(1)


    def update_rating(self, *args):
        self.rating_l.config(text = f"Rating: {str(int(self.rating_s.get()))}")


    def update_sophisticated(self, *args):
        self.sophisticated_l.config(text = f"Sophisticated: {str(int(self.sophisticated_s.get()))}")


    def lift_screen(self):
        self.parent.deiconify() # doesn't bring the window to front ! 
        self.parent.attributes("-topmost", True) # window needs to be visible already, e.g. self.parent.deiconify()
        self.parent.attributes("-topmost", False)


    def add_song_to_database(self):
        if self.song_e.get() == "": 
            self.add_song_lf.config(text = "Youtube-DL: No metadata entered in fields", fg = 'red', bg = self.BACKGROUND_COLOR)
            return

        meta = {}
        meta['song'] = self.song_e.get()
        artists = []
        if ', ' in self.artist_e.get():
            for artist in self.artist_e.get().split(', '):
                artists.append(artist)
        else:
            artists = [self.artist_e.get()]
        meta['artist'] = artists
        meta['album'] = self.album_e.get()
        meta['release_year'] = int(self.release_year_e.get())
        meta['duration'] = int(self.duration_e.get())
        meta['year_added'] = int(self.year_added_e.get())
        meta['youtube_url'] = self.link_e.get()
        meta['type'] = self.type_cb.get()
        meta['language'] = self.language_cb.get()
        meta['genre'] = [self.genre_values[i] for i in self.genre_lb.curselection()]
        meta['emotion'] = [self.emotion_values[i] for i in self.emotion_lb.curselection()]
        meta['instrument'] = [self.instrument_values[i] for i in self.instrument_lb.curselection()]
        meta['vocal'] = [self.vocal_values[i] for i in self.vocal_lb.curselection()]
        meta['rating'] = int(self.rating_s.get())
        meta['sophisticated'] = int(self.sophisticated_s.get())
        meta['title'] = self.song_title
        meta['filepath'] = self.song_filepath 
        meta['tree_iid'] = self.meta_tree_iid
        meta['bpm'] = self.bpm
        meta['rationale'] = None # NOTE placeholder for future possibly 
        meta['downloaded'] = 1

        # add song to db, if successfull give user a message
        self.JSON.at[self.meta_tree_iid, 'filepath'] = self.song_filepath 
        updated = self.MDB.metadata_to_database(meta, self.JSON)
        # RELOAD JSON to immediately be able to use mixer buttons after download 
        self.JSON = self.MDB.load_database(self.MDB.database_path)

        if updated:
            self.add_song_lf.config(text = "Youtube-DL: Existing song metadata updated!", fg = 'green', bg = self.BACKGROUND_COLOR)
        else:
            self.add_song_lf.config(text = "Youtube-DL: Upload successful!", fg = 'green', bg = self.BACKGROUND_COLOR)
            
        self.tree.item(self.meta_tree_iid, tags = ('green',))
        self.playlist_tree.item(self.meta_tree_iid, tags = ('green',))
        # recolor trees based on tags after adding to database based on if downloaded
        self.recolor_trees()
        


    def add_all_songs_to_playlist(self):
        for iid in self.tree.get_children():
            values = self.tree.item(iid)['values']
            try:
                self.playlist_tree.insert(parent = '', index = 'end', iid = iid, text = iid, values = values, tags = self.tree.item(iid)['tags'])
                self.playlist_tree.tag_configure(self.LABEL_COLOR, foreground=self.LABEL_COLOR) 
                self.playlist_tree.tag_configure(self.ACCENT_COLOR_SECONDARY, foreground=self.ACCENT_COLOR_SECONDARY)
                self.playlist_lf.config(text = 'Playlist: Added all songs!', fg = 'green')
            except tk.TclError as e:
                self.playlist_lf.config(text = 'Playlist: at least one song was duplicate!', fg = 'orange')


    def add_songs_to_playlist(self, index = 'end'):
        for iid in self.tree.selection():
            values = self.tree.item(iid)['values']
            try:
                self.playlist_tree.insert(parent = '', index = index, iid = iid, text = iid, values = values, tags = self.tree.item(iid)['tags'])
                self.playlist_tree.tag_configure('green', foreground='green')
                self.playlist_tree.tag_configure(self.ACCENT_COLOR_SECONDARY, foreground=self.ACCENT_COLOR_SECONDARY)
                self.playlist_lf.config(text = 'Playlist: Added song!', fg = 'green')
                return True
            except tk.TclError as e:
                self.playlist_lf.config(text = 'Playlist: Cannot add duplicate song to playlist.', fg = 'red')
                return False


    def remove_all_songs_from_playlist(self):
        for iid in self.playlist_tree.get_children():
            self.playlist_tree.delete(iid)
        self.playlist_lf.config(text = 'Playlist: Removed all songs!', fg = 'green')


    def remove_songs_from_playlist(self):
        for iid in self.playlist_tree.selection():
            self.playlist_tree.delete(iid)
        self.playlist_lf.config(text = 'Playlist: Removed song!', fg = 'green')


    def check_playlist_name(self):
        if self.save_songs_to_playlist_e.get() == "":
            self.playlist_lf.config(text = 'Need a name to save the current playlist', fg = 'red') 
            return False
        accepted_str = 'qwertyuiopasdfghjklzxcvbnm1234567890-_+ '
        for char in self.save_songs_to_playlist_e.get():
            if str(char).lower() not in accepted_str:
                self.playlist_lf.config(text = f'Character {char} not accepted for playlist name, accepted characters are {accepted_str}', fg = 'red') 
                return False
        return True


    def save_mp3s_to_car_playlist_folder(self):
        if not self.check_playlist_name():
            return 
        iids = []
        for iid in self.playlist_tree.get_children():
            iids.append(int(iid))
        if iids == []:
            self.playlist_lf.config(text = 'There are no songs to save in a car playlist', fg = 'red') 
            return

        # create new folder for playlist 
        parent = Path(self.JSON.loc[iids[0]]['filepath']).parents[1] / 'car_playlists' / self.save_songs_to_playlist_e.get()
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as e:
            self.playlist_lf.config(text = f'Car playlist with name {self.save_songs_to_playlist_e.get()} already exists, please pick another name.', fg = 'red') 
            return
        # for all songs in playlist, if they are downloaded, copy them into the car_playlist folder 
        for iid in iids:
            if self.JSON.loc[iid]['downloaded']:
                my_file = self.JSON.loc[iid]['filepath']
                to_file = Path(parent, Path(self.JSON.loc[iid]['filepath']).stem + Path(self.JSON.loc[iid]['filepath']).suffix)
                copy(my_file, to_file)  # from shutil package
        self.playlist_lf.config(text = f'Car playlist successfuly created!', fg = 'green') 


    def save_songs_from_playlist(self, event = None):
        playlist_name = self.save_songs_to_playlist_e.get()
        if not self.check_playlist_name():
            return
        
        iids = {'iids': []}
        for iid in self.playlist_tree.get_children():
            iids['iids'].append(int(iid))
        if iids == []:
            self.playlist_lf.config(text = 'There are no songs to save in a playlist', fg = 'red') 
            return

        df = pd.DataFrame(iids)
        
        # check if playlist saved successfully
        succes = self.MDB.save_playlist_database(df, playlist_name)
        if succes:
            self.playlist_lf.config(text = 'Playlist successfully saved!', fg = 'green') 
        else:
            self.playlist_lf.config(text = 'Playlist with a similar name exists, try another name', fg = 'red') 

        # add playlist to playlists_tree for use right away 
        color = self.LABEL_COLOR
        playlist_path = self.PLAYLIST_PATH / f'{playlist_name}.json'
        self.playlist_list_tree.insert(parent = '', index = 'end', iid = playlist_path, text = playlist_path, tags = (color,), values = playlist_name)
        self.playlist_list_tree.tag_configure(self.LABEL_COLOR, foreground=self.LABEL_COLOR) 


    def get_annotations(self, iid = None):
        clip = self.clipboard_get()
        
        if 'youtube.com' in clip:
            # check for duplicate song 
            mp3s = []
            mp3s.extend(self.MUSIC_PATH.glob('**/*.mp3'))
            for mp3 in mp3s:
                if clip.split('watch?v=')[1] + '.mp3' in str(mp3):
                    if not messagebox.askokcancel(title = "Duplicate song!", message = "Do you want to redownload and update metadata of song?"):
                        return
            
            # success message
            self.playlist_lf.configure(text = 'Playlist: downloading song ...', fg = 'orange')
            # download and extract raw metadata
            raw_meta = self.MD.download_mp3(link = clip)
            # get filepath to sava in DB and load song into mixer 
            filepath = "{}\\{}.mp3".format(str(self.MUSIC_PATH), raw_meta['id'])

            # set filepath and tree_iid here to make it easier to know what database index needs to be updated and where the newly downloaded mp3 file is
            raw_meta['tree_iid'] = iid
            raw_meta['filepath'] = filepath

            # format raw metadata
            meta = self.MDB.raw_to_formatted_metadata(raw_meta)
            # adding formatted metadata to database then happens by clicking the 'Add to database' button! 

            # start playing song after download 
            player.Player.load_song(filepath)
            # reset song time and end time
            self.set_song_end_time(time = raw_meta['duration'])
            self.TIME = 0

            # success message
            self.playlist_lf.configure(text = 'Playlist: Download successfull, do not forget to update song metadata and press "Add to database"!', fg = 'green')

            self.set_gui_values_after_download(meta = meta)
        else:
            self.add_song_lf.config(text = "Youtube-DL: No Youtube link copied", fg = 'red', bg = self.BACKGROUND_COLOR)


    def set_volume_icon(self, volume):
        if volume == 0:
            self.player_sound_btn.config(image = self.player_mute_img)
        elif volume <= 33:
            self.player_sound_btn.config(image = self.player_sound_lowest_img)
        elif volume <= 66:
            self.player_sound_btn.config(image = self.player_sound_low_img)
        else:
            self.player_sound_btn.config(image = self.player_sound_img)


    def slide_volume(self, event, volume = None):
        if volume == None:
            volume = int(self.player_volume_s.get())
        else:
            self.player_volume_s.set(volume)
        self.set_volume_icon(volume)
        player.Player.set_volume(volume/100)
        if volume != 0:
            self.VOLUME = volume
        

    def mute_unmute(self):
        volume = int(self.player_volume_s.get())
        if volume == 0: # unmute
            self.set_volume_icon(self.VOLUME)
            self.player_volume_s.set(self.VOLUME)
            player.Player.set_volume(self.VOLUME/100)
        else: # mute
            self.VOLUME = volume
            self.player_sound_btn.config(image = self.player_mute_img)
            self.player_volume_s.set(0)
            player.Player.set_volume(0)
            
    
    def on_double_click_songlist_tree(self, event):
        iid = int(event.widget.focus())

        if not self.add_songs_to_playlist(index = 0):
            self.reset_song(iid = iid)
            self.playlist_lf.config(text = 'Playlist: playing!', fg = 'green')
            return
    	# check if song downloaded
        if self.JSON.loc[iid]['downloaded'] == False:
            # get YT url and use for download
            yt_url = self.JSON.loc[iid]['youtube_url']
            self.clipboard_clear()
            self.clipboard_append(yt_url)
            self.queue.put(f'gui-ydl.{iid}')
            return
        # if already downloaded get filepath, load song, and reset time, progressbar and volume 
        self.reset_song(iid = iid)
        self.playlist_lf.config(text = 'Playlist: playing!', fg = 'green')




    def on_single_click_songlist_tree(self, event):
        iid = int(self.tree.selection()[0])
        self.on_single_click_either_tree(iid = iid)

    def on_single_click_playlist_tree(self, event):
        iid = int(self.playlist_tree.selection()[0])
        self.on_single_click_either_tree(iid = iid)


    def on_single_click_either_tree(self, iid):
        # TODO adjust all self.add_song_lf type labelframe to having a ttk.Label as their labelwidget parameter and then use these configs to set style like normal
        self.add_song_lf.config(text = "Youtube-DL: Adjust metadata if needed") 
        self.add_song_lf_l.config(foreground = 'red', background = 'black')




        db = self.JSON.loc[iid]

        self.link_e.configure(state='normal')
        self.link_e.delete(0, tk.END)
        self.link_e.insert(0, db['youtube_url'])
        self.link_e.configure(state='disabled')
        self.song_e.delete(0, tk.END)
        self.song_e.insert(0, db['song'])
        self.artist_e.delete(0, tk.END)
        self.artist_e.insert(0, ', '.join(db['artist']))
        self.album_e.delete(0, tk.END)
        self.album_e.insert(0, db['album'] if db['album'] != None else "")
        self.release_year_e.delete(0, tk.END)
        self.release_year_e.insert(0, db['release_year'])
        self.year_added_e.delete(0, tk.END)
        self.year_added_e.insert(0, db['year_added'])
        self.duration_e.configure(state='normal')
        self.duration_e.delete(0, tk.END)
        self.duration_e.insert(0, db['duration'])
        self.duration_e.configure(state='disabled')
        self.year_added_e.configure(state='normal')
        self.year_added_e.delete(0, tk.END)
        self.year_added_e.insert(0, db['year_added'])
        self.year_added_e.configure(state='disabled')
        self.type_sv.set(db['type'])

        self.rating_s.set(db['rating'])
        self.sophisticated_s.set(db['sophisticated'])

        self.song_title = db['title']
        self.song_filepath = db['filepath']
        self.bpm = db['bpm'] 
        self.meta_tree_iid = iid

        def set_listboxes(db, values, listbox):
            listbox.selection_clear(0, 'end')
            for typ in db:
                for index, value in enumerate(values):
                    if typ == value:
                        listbox.selection_set(index)
        set_listboxes(db['genre'], self.genre_values, self.genre_lb)
        set_listboxes(db['emotion'], self.emotion_values, self.emotion_lb)
        set_listboxes(db['instrument'], self.instrument_values, self.instrument_lb)
        set_listboxes(db['vocal'], self.vocal_values, self.vocal_lb)

        def set_comboboxes(db, combobox, values): 
            if db == "":
                combobox.set("")
            else:
                for index, typ in enumerate(values):
                    if typ == db:
                        combobox.set(typ)
        set_comboboxes(db['language'], self.language_cb, self.language_values)
        set_comboboxes(db['type'], self.type_cb, self.type_values)


    def clear_filter_entries(self):
        # reattach all iids in songlist and clear detached list
        for iid in set(self.JSON.index):
            self.tree.reattach(iid, '', 'end')
        self.tree_detached.clear()
        
        self.link_e.configure(state='normal')
        self.link_e.delete(0, tk.END)
        self.link_e.configure(state='disabled')
        self.song_e.delete(0, tk.END)
        self.artist_e.delete(0, tk.END)
        self.album_e.delete(0, tk.END)
        self.release_year_e.delete(0, tk.END)
        self.year_added_e.delete(0, tk.END)
        self.duration_e.configure(state='normal')
        self.duration_e.delete(0, tk.END)
        self.year_added_e.configure(state='normal')
        self.year_added_e.delete(0, tk.END)
        self.genre_lb.select_clear(0, tk.END)
        self.emotion_lb.select_clear(0, tk.END)
        self.instrument_lb.select_clear(0, tk.END)
        self.vocal_lb.select_clear(0, tk.END)
        self.language_cb.current(0) 
        self.type_cb.current(0)

        self.rating_s.set(self.RATING_DEFAULT)
        self.sophisticated_s.set(self.SOPHISTICATED_DEFAULT)

        self.add_song_lf.config(text = "Youtube-DL: Adjust metadata for filtering!", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)


    def filter_using_entries(self):
        self.tree_detached = set(self.JSON.index)
        for iid in set(self.JSON.index):
            self.tree.detach(iid)

        # initialize
        df = self.JSON
        # vocal
        vocal = list(self.vocal_lb.curselection()) # tuple -> list
        if vocal != []:
            reattach_index = set(df.index)
            for voca in vocal:
                for index, values in df['vocal'].items(): # list
                    value = self.vocal_values[int(voca)]
                    if value not in values and self.vocal_lb.itemcget(index = voca, option = 'selectbackground') != self.ACCENT_COLOR_SECONDARY:
                        reattach_index.remove(index)
            for voca in vocal:
                for index, values in df['vocal'].items(): # list
                    value = self.vocal_values[int(voca)]            
                    if value in values and self.vocal_lb.itemcget(index = voca, option = 'selectbackground') == self.ACCENT_COLOR_SECONDARY:
                        if index in reattach_index:
                            reattach_index.remove(index)
            df = df.loc[reattach_index]
        # language
        language = self.language_cb.get() # string
        if language != '':
            reattach_index = set()
            for index, value in df['language'].items(): # list
                if language in value:
                    reattach_index.add(index)
            df = df.loc[reattach_index]
        # instrument
        instrument = list(self.instrument_lb.curselection()) # tuple -> list
        if instrument != []:
            reattach_index = set(df.index)
            for ins in instrument:
                for index, values in df['instrument'].items(): # list
                    value = self.instrument_values[int(ins)]
                    if value not in values and self.instrument_lb.itemcget(index = ins, option = 'selectbackground') != self.ACCENT_COLOR_SECONDARY:
                        reattach_index.remove(index)
            for ins in instrument:
                for index, values in df['instrument'].items(): # list
                    value = self.instrument_values[int(ins)]
                    if value in values and self.instrument_lb.itemcget(index = ins, option = 'selectbackground') == self.ACCENT_COLOR_SECONDARY:
                        if index in reattach_index:
                            reattach_index.remove(index)
            df = df.loc[reattach_index]
        # album
        album = self.album_e.get().lower() # string
        if album != '':
            reattach_index = set()
            for index, value in df['album'].items(): # string
                if album in value.lower():
                    reattach_index.add(index)
            df = df.loc[reattach_index]
        # type 
        typ = self.type_cb.get() # string
        if typ != '':
            reattach_index = set()
            for index, value in df['type'].items(): # string
                if typ == value:
                    reattach_index.add(index)
            df = df.loc[reattach_index]
        # emotion
        emotion = list(self.emotion_lb.curselection()) # tuple -> list
        if emotion != []:
            reattach_index = set(df.index)
            # if want emo but not there, remove 
            for emo in emotion:
                for index, values in df['emotion'].items(): # list
                    value = self.emotion_values[int(emo)]
                    if value not in values and self.emotion_lb.itemcget(index = emo, option = 'selectbackground') != self.ACCENT_COLOR_SECONDARY:
                        reattach_index.remove(index)
            # if dont want emo, but there, remove
            for emo in emotion:
                for index, values in df['emotion'].items(): # list
                    value = self.emotion_values[int(emo)]
                    if value in values and self.emotion_lb.itemcget(index = emo, option = 'selectbackground') == self.ACCENT_COLOR_SECONDARY:
                        if index in reattach_index:
                            reattach_index.remove(index)
            df = df.loc[reattach_index]
        # genre
        genre = list(self.genre_lb.curselection()) # tuple -> list
        if genre != []:
            reattach_index = set(df.index)
            for gen in genre:
                for index, values in df['genre'].items(): # list
                    value = self.genre_values[int(gen)]
                    if value not in values and self.genre_lb.itemcget(index = gen, option = 'selectbackground') != self.ACCENT_COLOR_SECONDARY:
                        reattach_index.remove(index)
            for gen in genre:
                for index, values in df['genre'].items(): # list
                    value = self.genre_values[int(gen)]
                    if value in values and self.genre_lb.itemcget(index = gen, option = 'selectbackground') == self.ACCENT_COLOR_SECONDARY:
                        if index in reattach_index:
                            reattach_index.remove(index)
            df = df.loc[reattach_index]
        # release year 
        release_year = self.release_year_e.get() # string -> int
        if release_year != '':
            release_year = int(release_year)
            reattach_index = set()
            for index, value in df['release_year'].items(): # int
                if release_year == value:
                    reattach_index.add(index)
            df = df.loc[reattach_index]
        # duration - >=
        duration = self.duration_e.get() # string -> int
        if duration != '':
            duration = int(duration)
            reattach_index = set()
            for index, value in df['duration'].items(): # int
                if duration >= int(value):
                    reattach_index.add(index)
            df = df.loc[reattach_index]
        # year added - TODO could add operator to specify desired behaviour, or format: time-time to sepcify range 
        year_added = self.year_added_e.get() # string -> int
        if year_added != '':
            reattach_index = set()
            for index, value in df['year_added'].items(): # int
                if year_added in str(value)[0:len(year_added)]:
                    reattach_index.add(index)
            df = df.loc[reattach_index]
        # song
        song = self.song_e.get().lower() # string
        if song != '':
            reattach_index = set()
            for index, value in df['song'].items(): # string
                if song in value.lower():
                    reattach_index.add(index)
            df = df.loc[reattach_index]
        # artist
        artist = self.artist_e.get().lower() # string
        if artist != '':
            reattach_index = set()
            for index, values in df['artist'].items(): # list
                for artists in values:
                    if artist in artists.lower():
                        reattach_index.add(index)
            df = df.loc[reattach_index]
        # sophisticated - >=
        sophisticated = self.sophisticated_s.get() # int 
        reattach_index = set()
        for index, value in df['sophisticated'].items(): # int
            if sophisticated <= value:
                reattach_index.add(index)
        df = df.loc[reattach_index]
        # rating - >=
        rating = self.rating_s.get() # int 
        reattach_index = set()
        for index, value in df['rating'].items(): # int
            if rating <= value:
                reattach_index.add(index)
        df = df.loc[reattach_index]

        for iid in set(df.index):
            self.tree.reattach(iid, '', 'end')


    def set_gui_values_after_download(self, meta):
        self.link_e.configure(state='normal')
        self.link_e.delete(0, tk.END)
        self.link_e.insert(0, meta['youtube_url'])
        self.link_e.configure(state='disabled')
        self.song_e.delete(0, tk.END)
        self.song_e.insert(0, meta['song'])
        self.artist_e.delete(0, tk.END)
        self.artist_e.insert(0, ', '.join(meta['artist']))
        self.album_e.delete(0, tk.END)
        self.album_e.insert(0, meta['album'] if meta['album'] != None else "")
        self.release_year_e.delete(0, tk.END)
        self.release_year_e.insert(0, meta['release_year'])
        self.year_added_e.delete(0, tk.END)
        self.year_added_e.insert(0, meta['year_added'])
        self.duration_e.configure(state='normal')
        self.duration_e.delete(0, tk.END)
        self.duration_e.insert(0, meta['duration'])
        self.duration_e.configure(state='disabled')
        self.year_added_e.configure(state='normal')
        self.year_added_e.delete(0, tk.END)
        self.year_added_e.insert(0, meta['year_added'])
        self.year_added_e.configure(state='disabled')
        self.type_sv.set(meta['type'])

        self.rating_s.set(self.RATING_DEFAULT)
        self.sophisticated_s.set(self.SOPHISTICATED_DEFAULT)

        self.song_title = meta['title']
        self.bpm = meta['bpm']
        self.song_filepath = meta['filepath']
        self.meta_tree_iid = meta['tree_iid']
        
        self.add_song_lf.config(text = "Youtube-DL: Adjust metadata if needed", fg = self.LABEL_COLOR, bg = self.BACKGROUND_COLOR)


    def on_double_click_playlist_tree(self, event):
        self.JSON = self.MDB.load_database(self.MDB.database_path)

        iid = int(event.widget.focus())

        self.playlist_tree.move(iid, self.playlist_tree.parent(iid), 0)

        if self.JSON.loc[iid]['downloaded'] == False:
            # get YT url and use for download
            yt_url = self.JSON.loc[iid]['youtube_url']
            self.clipboard_clear()
            self.clipboard_append(yt_url)
            self.queue.put(f'gui-ydl.{iid}')
            return

        self.reset_song(iid = iid)
        self.playlist_lf.config(text = 'Playlist: playing!')
        

    def unpause_song(self):
        self.player_playpause_btn.config(image=self.player_play_img)
        player.Player.unpause()
        self.player_playpause_btn.config(text='play')


    def pause_song(self):
        self.player_playpause_btn.config(image=self.player_pause_img)
        player.Player.pause()
        self.player_playpause_btn.config(text='pause')


    def playpause_song(self):
        playpause = self.player_playpause_btn.cget('text')
        self.player_playpause_btn.config(image=self.player_play_img) if playpause == 'play' else self.player_playpause_btn.config(image=self.player_pause_img)
        player.Player.pause() if playpause == 'play' else player.Player.unpause()
        self.player_playpause_btn.config(text='pause') if playpause == 'play' else self.player_playpause_btn.config(text='play')


    def shuffle_playlist(self):
        if self.playlist_tree.get_children() == ():
            self.playlist_lf.config(text = 'Playlist: no songs to shuffle', fg = 'red')
            return
        
        original_order = list(self.playlist_tree.get_children())
        new_order = sample(original_order, len(original_order))

        values = {}
        for iid in original_order:
            values[iid] = [self.playlist_tree.item(iid)['values'], self.playlist_tree.item(iid)['tags']]
            self.playlist_tree.delete(iid)
        for iid in new_order:
            self.playlist_tree.insert(parent = '', index = 0, iid = iid, text = iid, values = values[iid][0], tags = values[iid][1])
            
        # get iid of second to last (new first) item
        iid_new_first = int(self.playlist_tree.get_children()[0])
        # download if not downloaded, else load and play song
        if not self.JSON.loc[iid_new_first]['downloaded']: 
            # get YT url and use for download
            yt_url = self.JSON.loc[iid_new_first]['youtube_url']
            self.clipboard_clear()
            self.clipboard_append(yt_url)
            self.queue.put(f'gui-ydl.{iid_new_first}') 
        else:
            # load new first item of tree
            self.reset_song(iid = iid_new_first)

    def set_previous_song(self):
        if self.playlist_tree.get_children() == ():
            self.playlist_lf.config(text = 'Playlist: no songs in playlist', fg = 'red')
            return
        # get iid of first item
        iid_last = int(self.playlist_tree.get_children()[-1])
        # get values and tags of item
        last_values = self.playlist_tree.item(iid_last)['values']
        last_tags = self.playlist_tree.item(iid_last)['tags']
        # delete first item and insert back at bottom
        self.playlist_tree.delete(iid_last)
        self.playlist_tree.insert(parent = '', index = 0, iid = iid_last, text = iid_last, values = last_values, tags = last_tags)

        # get iid of second to last (new first) item
        iid_second = int(self.playlist_tree.get_children()[0])
        # download if not downloaded, else load and play song
        if not self.JSON.loc[iid_second]['downloaded']: 
            # get YT url and use for download
            yt_url = self.JSON.loc[iid_second]['youtube_url']
            self.clipboard_clear()
            self.clipboard_append(yt_url)
            self.queue.put(f'gui-ydl.{iid_second}') 
        else:
            # load new first item of tree
            self.reset_song(iid = iid_second)


    def set_next_song(self):
        if self.playlist_tree.get_children() == ():
            self.playlist_lf.config(text = 'Playlist: no songs in playlist', fg = 'red')
            return
        # get iid of first item
        iid_first = int(self.playlist_tree.get_children()[0])
        # get values and tags of item
        first_values = self.playlist_tree.item(iid_first)['values']
        first_tags = self.playlist_tree.item(iid_first)['tags']
        # delete first item and insert back at bottom
        self.playlist_tree.delete(iid_first)
        self.playlist_tree.insert(parent = '', index = 'end', iid = iid_first, text = iid_first, values = first_values, tags = first_tags)

        # get iid of second (new first) item
        iid_second = int(self.playlist_tree.get_children()[0])
        # download if not downloaded, else load and play song
        if not self.JSON.loc[iid_second]['downloaded']: 
            # get YT url and use for download
            yt_url = self.JSON.loc[iid_second]['youtube_url']
            self.clipboard_clear()
            self.clipboard_append(yt_url)
            self.queue.put(f'gui-ydl.{iid_second}') 
        else:
            # load new first item of tree
            self.reset_song(iid = iid_second)
            

    def get_formatted_time(self, time):
        minutes = int(time / 60)
        seconds = int(time % 60)
        if seconds < 10:
            seconds = f'0{seconds}'
        return f'{minutes}:{seconds}'


    def set_song_end_time(self, time):
        self.player_progress_end_l.config(text=self.get_formatted_time(time))
        self.player_progress_s.config(to = time)


    def set_song_label_slider(self):
        self.player_progress_start_l.config(text=self.get_formatted_time(self.TIME))
        self.player_progress_s.set(self.TIME)


    def reset_song(self, iid, song_start = 0):
        self.set_song_end_time(time = self.JSON.loc[iid]['duration'])
        filepath = self.JSON.loc[iid]['filepath']

        player.Player.load_song(filepath = filepath, start = song_start)
        playpause = self.player_playpause_btn.cget('text')
        if playpause == 'pause':
            player.Player.pause()
        
        self.TIME = song_start
        self.TIME_MEMORY = 0
        if self.VOLUME == 0:
            player.Player.set_volume(20)
            self.player_volume_s.set(20)
        self.set_volume_icon(self.VOLUME)


    def set_song_progression(self, event):
        # get slider position relative to song length
        slider_value = int(self.player_progress_s.get())
        
        # if music still ongoing after its noted song duration
        if self.TIME > self.player_progress_s.cget('to'):
            # increase song end time 
            self.set_song_end_time(self.TIME)
            # save new song end time in music database (MDB via self.JSON)
            iid = int(self.playlist_tree.get_children()[0])
            self.JSON.at[iid, 'duration'] = self.TIME
            self.MDB.save_database(self.JSON)
        # on click (or drag) of the song progression bar 
        elif slider_value != self.TIME:
            ## aka memory becomes get.pos()
            self.TIME_MEMORY += slider_value - self.TIME
            iid = int(self.playlist_tree.get_children()[0])
            self.reset_song(iid = iid, song_start = slider_value)
            self.TIME = slider_value
            self.set_song_label_slider()


    def check_queue(self):
        song_playing = player.Player.check_song_end()
        # increment time and label and slider if song is playing, otherwise play next song in playlist
        if song_playing: 
            playpause = self.player_playpause_btn.cget('text')
            if playpause == 'play':
                # increase time passed
                self.TIME += 1
                self.set_song_label_slider()
        else:
            self.set_next_song()

        # call self to check queue again every second while GUI and player are active 
        self.after(1000, self.check_queue)

        while not self.queue.empty():
            try:
                msg = self.queue.get(block = False)
                # hotkey used to skip seconds back or forward in song
                if 'seconds changed:' in msg:
                    if not song_playing:
                        return
                    time_change = msg.split(' ')[2]
                    iid = int(self.playlist_tree.get_children()[0])
                    song_duration = self.JSON.loc[iid]['duration']
                    if self.TIME + int(time_change) > song_duration:
                        self.set_next_song()
                    elif song_playing: 
                        self.TIME += int(time_change)
                        self.set_song_label_slider()
                # hotkey used when copied YT link
                if msg == 'gui-ydl':
                    self.lift_screen()
                    self.get_annotations()
                # double clicked a song that still needs to be downloaded
                if 'gui-ydl.' in msg: 
                    self.lift_screen()
                    iid = msg.split('.')[1]
                    self.get_annotations(iid)
                if 'pause-unpause' == msg:
                    self.playpause_song()
                if 'exit-app' == msg:
                    exit()
                if 'replay-song' == msg:
                    self.reset_song(iid = int(self.playlist_tree.get_children()[0]))
                if 'next-song' == msg:
                    self.set_next_song()
                if 'previous-song' == msg:
                    self.set_previous_song()
                if 'shuffle-playlist' == msg:
                    self.shuffle_playlist()
                if 'volume' in msg:
                    self.slide_volume(event = None, volume = player.Player.get_volume()*100)
            except queue.Empty:
                pass


if __name__ == '__main__':

    root = tk.Tk() 
    root.title("Mausic")
    root.iconphoto(True, tk.PhotoImage(file = Path(top_level_path() / 'data' / 'resources' / 'icons' / 'Mausic logo.png'), master=root))
    # root.configure(background = 'black')
    # root.geometry('1250x750')ñ
    root.resizable(0, 0)
    # root.minsize(500, 500)
    root.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
    app = UserInterface(root)
    # app.configure(background = '#ffffff') # TODO does this help ? 

    root.mainloop()



# TODO add label above/below song progression slider to show title of currently playing song 

# TODO check tkinter themes/styles again, now that the screen doesn't pop up because I initialize it in a different place! 


# TODO create delete button to delete song from songlist and database 

# TODO create update button to update playlist 

# TODO the + and - buttons are going to have functionality for song rating which gets saved instantly in JSON MDB or temp MDB which updates main JSON MDB at certain intervals
# TODO create ? button that shows popup screen for all hotkeys 






# TODO once all songs green, loop over all downloaded entries and perform BPM calculation once
# TODO use pydub to slice audio (when songs are silent at begin or end, or want to make a meme small fragment easily)

# TODO need a way to add music from mp3 instead of YT 

# TODO customize style and colors: https://tkdocs.com/tutorial/styles.html


# TODO artists to add
# wudstik 
# maaike ouboter
# the white stripes
# gers pardoel
# the police  
# eminem 
# billy talent 
# daft punk