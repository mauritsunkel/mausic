import tkinter as tk
import player
import queue

from download_music import Music_download as md
from threading import Thread, Lock

from tkinter import ttk 


class UserInterface(tk.Frame):
    objects = []
    RATING_DEFAULT = 75
    SOPHISTICATED_DEFAULT = 50

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
        self.link_l = tk.Label(self.add_song_lf, text = "Link")
        self.link_e = tk.Entry(self.add_song_lf)

        # TODO then add a shortcut such that after copying the youtube link, you can put the GUI in front, paste clipboard in link and start getting meta info to fill in! 
        # TODO add func: on click label paste whats copied on clipboard to link_e and with youtube-dl get meta information to prep many values (if no link in clipboard or in entry, error msg
        print("clipboard", self.clipboard_get())
        





        # TODO add func: on click song or artist label -> swap entry values 
        self.song_l = tk.Label(self.add_song_lf, text = "Song")
        self.song_e = tk.Entry(self.add_song_lf)
        self.artist_l = tk.Label(self.add_song_lf, text = "Artist")
        self.artist_e = tk.Entry(self.add_song_lf)
        self.genre_l = tk.Label(self.add_song_lf, text = "Genre")

        self.genre_f = tk.Frame(self.add_song_lf)
        self.genre_f.grid(row = 8, column = 1)
        self.genre_sb = tk.Scrollbar(self.genre_f)
        self.genre_sb.pack(side = 'right', fill = 'y')
        self.genre_lb = tk.Listbox(self.genre_f, height = 5, width = 15, yscrollcommand = self.genre_sb.set, selectmode = "multiple")
        self.genre_values = sorted(["Electric", "Jazz", "Comedy", "Pop", "Singer songwriter", "Rock", "Metal", "Soul", "House"])
        for i in range(0, len(self.genre_values)):
            self.genre_lb.insert(i, self.genre_values[i])
        self.genre_lb.pack(side = 'left')
        self.genre_sb.config(command = self.genre_lb.yview)

        
        self.album_l = tk.Label(self.add_song_lf, text = "Album")
        self.album_e = tk.Entry(self.add_song_lf)
        self.type_l = tk.Label(self.add_song_lf, text = "Type")
        self.type_cb = ttk.Combobox(self.add_song_lf, state = 'readonly', values = ["", "Single", "EP", "Cover", "Remix", "Mashup"])
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

        
        self.emotion_l = tk.Label(self.add_song_lf, text = "Emotion")

        # TODO create a dropdown menu for categorical emotions 
        self.emotion_f = tk.Frame(self.add_song_lf)
        self.emotion_f.grid(row = 8, column = 3)
        self.emotion_sb = tk.Scrollbar(self.emotion_f)
        self.emotion_sb.pack(side = 'right', fill = 'y')
        self.emotion_lb = tk.Listbox(self.emotion_f, height = 5, width = 15, yscrollcommand = self.emotion_sb.set, selectmode = "multiple")
        self.emotion_values = sorted(["Happy", "Sad", "Love", "Chill", "Hard"])
        for i in range(0, len(self.emotion_values)):
            self.emotion_lb.insert(i, self.emotion_values[i])
        self.emotion_lb.pack(side = 'left')
        self.emotion_sb.config(command = self.emotion_lb.yview)



        self.bpm_l = tk.Label(self.add_song_lf, text = "BPM")
        self.bpm_e = tk.Entry(self.add_song_lf, state = 'disabled')
        self.instrument_l = tk.Label(self.add_song_lf, text = "Instrument(s)")

        self.instrument_f = tk.Frame(self.add_song_lf)
        self.instrument_f.grid(row = 8, column = 5)
        self.instrument_sb = tk.Scrollbar(self.instrument_f)
        self.instrument_sb.pack(side = 'right', fill = 'y')
        self.instrument_lb = tk.Listbox(self.instrument_f, height = 5, width = 15, yscrollcommand = self.instrument_sb.set, selectmode = "multiple")
        self.listbox_values = ["Guitar", "Piano"]
        for i in range(0, len(self.listbox_values)):
            self.instrument_lb.insert(i, self.listbox_values[i])
        self.instrument_lb.pack(side = 'left')
        self.instrument_sb.config(command = self.instrument_lb.yview)

        self.vocal_l = tk.Label(self.add_song_lf, text = "Vocal")
        self.vocal_cb = ttk.Combobox(self.add_song_lf, state = 'readonly', values = ["", "Female", "Male", "Duo", "Trio", "Quartet", "Barbershop", "Multiple", "Acapella"])
        self.vocal_cb.current(0)
        self.language_l = tk.Label(self.add_song_lf, text = "Language")
        self.language_cb = ttk.Combobox(self.add_song_lf, state = 'readonly', values = ["", "English", "Dutch", "French", "German", "Asian"])
        self.language_cb.current(0)
        self.year_added_l = tk.Label(self.add_song_lf, text = "Year added")
        self.year_added_e = tk.Entry(self.add_song_lf, state = 'disabled')

        self.link_l.grid(row = 0, column = 0, sticky = 'e')
        self.link_e.grid(row = 0, column = 1)
        self.song_l.grid(row = 1, column = 0, sticky = 'e')
        self.song_e.grid(row = 1, column = 1)
        self.artist_l.grid(row = 2, column = 0, sticky = 'e')
        self.artist_e.grid(row = 2, column = 1)
        self.album_l.grid(row = 3, column = 0, sticky = 'e')
        self.album_e.grid(row = 3, column = 1)
        self.release_year_l.grid(row = 4, column = 0, sticky = 'e')
        self.release_year_e.grid(row = 4, column = 1)
        self.rating_l.grid(row = 0, column = 2, rowspan = 2, sticky = 'e')
        self.rating_s.grid(row = 0, column = 3, rowspan = 2)
        self.sophisticated_l.grid(row = 3, column = 2, rowspan = 2, sticky = 'e')
        self.sophisticated_s.grid(row = 3, column = 3, rowspan = 2)
        
        
        
        self.emotion_l.grid(row = 8, column = 2, sticky = 'e')

        
        self.bpm_l.grid(row = 3, column = 4, sticky = 'e')
        self.bpm_e.grid(row = 3, column = 5)

        self.type_l.grid(row = 0, column = 4, sticky = 'e')
        self.type_cb.grid(row = 0, column = 5)
        self.vocal_l.grid(row = 1, column = 4, sticky = 'e')
        self.vocal_cb.grid(row = 1, column = 5)
        self.language_l.grid(row = 2, column = 4, sticky = 'e')
        self.language_cb.grid(row = 2, column = 5)
        self.duration_l.grid(row = 4, column = 4, sticky = 'e')
        self.duration_e.grid(row = 4, column = 5)
        self.year_added_l.grid(row = 7, column = 4, sticky = 'e')
        self.year_added_e.grid(row = 7, column = 5)
        self.instrument_l.grid(row = 8, column = 4, sticky = 'e')

        self.genre_l.grid(row = 8, column = 0, sticky = 'e')

        
        
    def update_rating(self, *args):
        self.rating_l.config(text = "Rating: {}".format(str(self.rating_s.get())))
    def update_sophisticated(self, *args):
        self.sophisticated_l.config(text = "Sophisticated: {}".format(str(self.sophisticated_s.get())))

    def lift_screen(self):
        print(1234)
        self.parent.deiconify() # doesn't bring the window to front ! 
        self.parent.attributes("-topmost", True) # window needs to be visible already, e.g. self.parent.deiconify()
        self.parent.attributes("-topmost", False)
        # self.lift() # does not work? 

    def get_annotations(self):
        clip = self.clipboard_get()
        if 'youtube.com' in clip:
            meta = md.download_annotations(link = clip)
            print(meta)
            # TODO look in update_database metadata_to_database function for how to extract meta info and put it into the GUI
            # TODO from GUI, change meta dictionary and pass to metadata_to_database while also just downloading without extracting meta info again! 
        else:
            # TODO print warning message to user! 
            print('WRONG LINK:', clip)

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
    # root.iconphoto(True, tk.PhotoImage(file = "resources\\figures\MEA_icon.png"))
    # root.configure(background = 'red')
    # root.geometry('1250x750')
    root.resizable(0, 0)
    # root.minsize(500, 500)
    root.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
    app = UserInterface(root)
    # app.configure(background = '#dddddd')

    root.mainloop()


# TODO 'He even covers running the GUI as a separate program with sockets.' book --> https://www.amazon.com/Programming-Python-Powerful-Object-Oriented/dp/0596158106 
## give it a look for another solution, if it means it doesn't need us checking a queue every x milliseconds then that sounds like a win to me! 

# TODO look at TODO in test-queue.py under utils/ 


# TODO look into this presentation tutorial by David Beazley: http://www.dabeaz.com/usenix2009/concurrent/ 
## check this before - only at synch/locking part?: https://www.techbeamers.com/python-multithreading-concepts/#python-multithreading-8211-synchronizing-threads 


# TODO look into threading Queues more? : https://www.youtube.com/watch?v=NwH0HvMI4EA
# TODO look into threading locking/synchronizing more? : https://www.youtube.com/watch?v=SDAkQq17S2Q
## https://stackoverflow.com/questions/52073973/how-do-i-update-the-gui-from-another-thread-using-python
# TODO learn more about fundamental threading? 

# TODO worst case scenario: run GUI and player in same scripts
## however, solving this here would also solve progressbar functionality for MEA project! 



# TODO folders entry: specialized function to change folder globally, which simultaneously moves all currently stored files! 

# TODO save this project on Github! also to safeguard music database JSOn and playlists 