import tkinter as tk
import player
import queue
import sys
import os
import update_database as ud
import download_music as dm 
import ctypes

from threading import Thread, Lock
from tkinter import messagebox
from tkinter import ttk 
from utils.top_level_locator import top_level_path
from pathlib import Path

# tell windows that python(w) is a host and not an application before it gets grouped as such
# therefore TASKBAR ICON will be set by tkinter now
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('arbitrary string')

# allows application to work without console in the background (pythonw.exe)
## it prevents print() and sys.stdout write calls which apparently block py2 and py3 in pyw mode 
if sys.executable.endswith("pythonw.exe"):
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.path.join(os.getenv("TEMP"), "stderr-"+os.path.basename(sys.argv[0])), "w")

class UserInterface(tk.Frame):
    objects = []
    RATING_DEFAULT = 75
    SOPHISTICATED_DEFAULT = 50
    MDB = ud.MusicDatabase()

    def __init__(self, parent = None):
        tk.Frame.__init__(self, parent)
        UserInterface.objects.append(self)
        self.parent = parent
        self.pack(fill = 'both', expand = True)

        self.initialize_layout()
        self.initialize_add_song()

        self.queue = queue.Queue()
        self.parent.after(1000, self.check_queue)

        def run_player():
            player.Player(play_volume = .0, song_index = 0, queue = self.queue)

        music_player_T = Thread(target=run_player, daemon = True)
        music_player_T.start()

        # player.Player(play_volume = .2, song_index = 0, queue = self.queue)
        


    def initialize_layout(self):
        self.add_song_lf = tk.LabelFrame(self, text = "Add song")
        self.playlists_lf = tk.LabelFrame(self, text = "Playlists")
        self.filters_lf = tk.LabelFrame(self, text = "Filters")
        self.meta_information_lf = tk.LabelFrame(self, text = "Meta info")
        self.player_lf = tk.LabelFrame(self, text = "Player")
        
        self.add_song_lf.grid(row = 0, column = 0, rowspan = 3, columnspan = 1)
        self.playlists_lf.grid(row = 1, column = 0, rowspan = 1, columnspan = 2)
        self.filters_lf.grid(row = 1, column = 1, rowspan = 2, columnspan = 1)
        self.meta_information_lf.grid(row = 2, column = 1, rowspan = 2, columnspan = 1)
        self.player_lf.grid(row = 3, column = 0, rowspan = 3, columnspan = 1)

    def initialize_add_song(self):
        self.add_song_listbox_height = 12

        self.link_l = tk.Label(self.add_song_lf, text = "Link")
        self.link_e = tk.Entry(self.add_song_lf, state = 'disabled')


        try:
            print("clipboard", self.clipboard_get())
        except:
            pass
        
        self.song_l = tk.Label(self.add_song_lf, text = "Song")
        self.song_e = tk.Entry(self.add_song_lf)
        self.song_l.bind('<Button-1>', self.switch_song_artists)
        self.artist_l = tk.Label(self.add_song_lf, text = "Artist(s)")
        self.artist_e = tk.Entry(self.add_song_lf)
        self.artist_l.bind('<Button-1>', self.switch_song_artists)
        self.genre_l = tk.Label(self.add_song_lf, text = "Genre(s)")
        self.genre_f = tk.Frame(self.add_song_lf)
        self.genre_f.grid(row = 8, column = 1, sticky = 'w')
        self.genre_sb = tk.Scrollbar(self.genre_f)
        self.genre_sb.pack(side = 'right', fill = 'y')
        self.genre_lb = tk.Listbox(self.genre_f, exportselection = 0, height = self.add_song_listbox_height, width = 15, yscrollcommand = self.genre_sb.set, selectmode = "multiple")
        self.genre_values = sorted(["Electric", "Jazz", "Comedy", "Pop", "Singer songwriter", "Rock", "Metal", "Soul", "House", "Vocal", "Rap", "Country"])
        for i in range(0, len(self.genre_values)):
            self.genre_lb.insert(i, self.genre_values[i])
        self.genre_lb.pack(side = 'left')
        self.genre_sb.config(command = self.genre_lb.yview)
        self.add_song_user_l = tk.Label(self.add_song_lf)
        
        self.album_l = tk.Label(self.add_song_lf, text = "Album")
        self.album_e = tk.Entry(self.add_song_lf)
        self.type_l = tk.Label(self.add_song_lf, text = "Type")
        self.type_sv = tk.StringVar()
        self.type_cb = ttk.Combobox(self.add_song_lf, textvariable = self.type_sv, state = 'readonly', values = ["", "Single", "EP", "Cover", "Remix", "Mashup"])
        self.type_cb.current(0)
        self.release_year_l = tk.Label(self.add_song_lf, text = "Release year")
        self.release_year_e = tk.Entry(self.add_song_lf)
        self.duration_l = tk.Label(self.add_song_lf, text = "Duration (s)")
        self.duration_e = tk.Entry(self.add_song_lf, state = 'disabled')
        self.rating_l = tk.Label(self.add_song_lf, text = "Rating: {}".format(self.RATING_DEFAULT))
        self.rating_s = tk.Scale(self.add_song_lf, from_ = 0, to = 100, resolution = 1, command = self.update_rating, orient = 'horizontal')
        self.rating_s.set(self.RATING_DEFAULT)
        
        self.sophisticated_l = tk.Label(self.add_song_lf, text = "Sophisticated: {}".format(self.SOPHISTICATED_DEFAULT), width = 14)
        self.sophisticated_s = tk.Scale(self.add_song_lf, from_ = 0, to = 100, resolution = 1, command = self.update_sophisticated, orient = 'horizontal')
        self.sophisticated_s.set(self.SOPHISTICATED_DEFAULT)

        
        self.emotion_l = tk.Label(self.add_song_lf, text = "Emotion(s)")

        
        self.emotion_f = tk.Frame(self.add_song_lf)
        self.emotion_f.grid(row = 8, column = 3, sticky = 'w')
        self.emotion_sb = tk.Scrollbar(self.emotion_f)
        self.emotion_sb.pack(side = 'right', fill = 'y')
        self.emotion_lb = tk.Listbox(self.emotion_f, exportselection=0, height = self.add_song_listbox_height, width = 15, yscrollcommand = self.emotion_sb.set, selectmode = "multiple")
        self.emotion_values = sorted(["Happy", "Sad", "Love", "Chill", "Chaos", "Gaming", "Focus", "Visualization", "Nostalgia"])
        for i in range(0, len(self.emotion_values)):
            self.emotion_lb.insert(i, self.emotion_values[i])
        self.emotion_lb.pack(side = 'left')
        self.emotion_sb.config(command = self.emotion_lb.yview)

        self.instrument_l = tk.Label(self.add_song_lf, text = "Instrument(s)")
        self.instrument_f = tk.Frame(self.add_song_lf)
        self.instrument_f.grid(row = 8, column = 5, sticky = 'w')
        self.instrument_sb = tk.Scrollbar(self.instrument_f)
        self.instrument_sb.pack(side = 'right', fill = 'y')
        self.instrument_lb = tk.Listbox(self.instrument_f, exportselection=0, height = self.add_song_listbox_height, width = 15, yscrollcommand = self.instrument_sb.set, selectmode = "multiple")
        self.instrument_values = sorted(["Guitar", "Piano", 'Flute', 'Drum', 'Harmonica', 'Saxophone', 'Trumpet', 'Violin', 'Bass'])
        for i in range(0, len(self.instrument_values)):
            self.instrument_lb.insert(i, self.instrument_values[i])
        self.instrument_lb.pack(side = 'left')
        self.instrument_sb.config(command = self.instrument_lb.yview)

        self.vocal_l = tk.Label(self.add_song_lf, text = "Vocal(s)")
        self.vocal_f = tk.Frame(self.add_song_lf)
        self.vocal_f.grid(row = 8, column = 7, sticky = 'w')
        self.vocal_sb = tk.Scrollbar(self.vocal_f)
        self.vocal_sb.pack(side = 'right', fill = 'y')
        self.vocal_lb = tk.Listbox(self.vocal_f, exportselection=0, height = self.add_song_listbox_height, width = 15, yscrollcommand = self.vocal_sb.set, selectmode = "multiple")
        self.vocal_values = ["Female", "Male", "Duo", "Trio", "Quartet", "Barbershop", "Multiple", "Acapella"]
        for i in range(0, len(self.vocal_values)):
            self.vocal_lb.insert(i, self.vocal_values[i])
        self.vocal_lb.pack(side = 'left')
        self.vocal_sb.config(command = self.vocal_lb.yview)
        self.vocal_lb.bind("<<ListboxSelect>>", self.set_vocal_default)

        self.language_l = tk.Label(self.add_song_lf, text = "Language")
        self.language_cb = ttk.Combobox(self.add_song_lf, state = 'readonly', values = ["", "English", "Dutch", "French", "German", "Asian"])
        self.language_cb.current(0)
        self.year_added_l = tk.Label(self.add_song_lf, text = "Year added")
        self.year_added_e = tk.Entry(self.add_song_lf, state = 'disabled')

        self.add_database_b = tk.Button(self.add_song_lf, text = "Add to database", command = self.add_song_to_database)

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
        self.add_song_user_l.grid(row = 0, column = 4, columnspan = 3)
        
        self.genre_l.grid(row = 8, column = 0, sticky = 'e')
        self.emotion_l.grid(row = 8, column = 2, sticky = 'e')

        self.type_l.grid(row = 2, column = 6, sticky = 'e')
        self.type_cb.grid(row = 2, column = 7, sticky = 'w')
        self.vocal_l.grid(row = 8, column = 6, sticky = 'e')
        self.language_l.grid(row = 3, column = 6, sticky = 'e')
        self.language_cb.grid(row = 3, column = 7, sticky = 'w')
        self.link_l.grid(row = 3, column = 4, sticky = 'e')
        self.link_e.grid(row = 3, column = 5, sticky = 'w')
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

    def set_vocal_default(self, *args):
        if self.language_cb.get() == '':
            self.language_cb.current(1)
        
    def update_rating(self, *args):
        self.rating_l.config(text = "Rating: {}".format(str(self.rating_s.get())))
    def update_sophisticated(self, *args):
        self.sophisticated_l.config(text = "Sophisticated: {}".format(str(self.sophisticated_s.get())))

    def lift_screen(self):
        self.parent.deiconify() # doesn't bring the window to front ! 
        self.parent.attributes("-topmost", True) # window needs to be visible already, e.g. self.parent.deiconify()
        self.parent.attributes("-topmost", False)
        # XXX self.lift() # does not work? 

    def add_song_to_database(self):
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
        meta['bpm'] = None # NOTE will be calculated in update function
        meta['rationale'] = None # NOTE placeholder for future possibly 
        meta['downloaded'] = False

        # add song to db, if successfull print message
        if UserInterface.MDB.metadata_to_database(meta):
            self.add_song_user_l.config(text = "Existing song metadata updated!", fg = 'green')
        else:
            self.add_song_user_l.config(text = "Upload successful!", fg = 'green')
            

    def set_add_song_values(self, meta, youtube_link):
        if meta['album'] != None:
            width = max(len(meta['song']), len(', '.join(meta['artist'])), len(meta['album'])) + 3
        else:
            width = max(len(meta['song']), len(', '.join(meta['artist']))) + 3

        self.link_e.configure(state='normal')
        self.link_e.delete(0, tk.END)
        self.link_e.insert(0, youtube_link)
        self.link_e.configure(state='disabled')
        self.song_e.config(width = width)
        self.song_e.delete(0, tk.END)
        self.song_e.insert(0, meta['song'])
        self.artist_e.config(width = width)
        self.artist_e.delete(0, tk.END)
        self.artist_e.insert(0, ', '.join(meta['artist']))
        self.album_e.config(width = width)
        self.album_e.delete(0, tk.END)
        self.album_e.insert(0, meta['album'] if meta['album'] != None else "")
        self.release_year_e.config(width = width)
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

        self.song_title = meta['title']
        self.song_filepath = meta['filepath']
        
        self.add_song_user_l.config(text = "Adjust metadata if needed", fg = 'black')

    def get_annotations(self):
        clip = self.clipboard_get()
        
        if 'youtube.com' in clip:
            raw_meta = dm.MusicDownload.download_annotations(link = clip)
            meta = self.MDB.raw_to_formatted_metadata(raw_meta)

            if self.MDB.check_duplicate_song(raw_meta['webpage_url']):
                if not messagebox.askokcancel(title = "Duplicate song!", message = "Do you want to update metadata of song?"):
                    return

            # if song longer than 10 minutes, validate by user
            if meta['duration'] >= 10 * 60:
                if not messagebox.askokcancel(title = "Long song!", message = "Is this a single song?"):
                    return
    
            self.set_add_song_values(meta = meta, youtube_link = clip)






            # TODO maybe put ydl link as filename such that its always unique? 
        else:
            self.add_song_user_l.config(text = "No youtube link on clipboard", fg = 'red')

    def check_queue(self):
        try:
            msg = self.queue.get(block = False)
            print('queue msg:', msg)
            if msg == 'gui-ydl':
                self.lift_screen()
                self.get_annotations()
        except queue.Empty:
            pass
        finally:
            self.parent.after(1000, self.check_queue)
            


if __name__ == '__main__':

    root = tk.Tk() 
    root.title("Mausic")
    root.iconphoto(True, tk.PhotoImage(file = Path(top_level_path() / 'data' / 'resources' / 'music_logo.png')))
    # root.configure(background = 'red')
    # root.geometry('1250x750')
    root.resizable(0, 0)
    # root.minsize(500, 500)
    root.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
    app = UserInterface(root)
    # app.configure(background = '#dddddd')

    root.mainloop()




# TODO create view tree from current songs in JSON db

# TODO artists to add
# wudstik 
# the white stripes
# gers pardoel
# the police  
# eminem 
# billy talent 
# daft punk