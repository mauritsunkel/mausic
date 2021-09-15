# from threading import Thread, Lock
from pygame import mixer # time,
from pynput.keyboard import Key, KeyCode, Listener


class Player():
    # objects = []
    time_start = 0
    time_memory = 0

    def __init__(self, play_volume, song_index, queue, filepath):
        self.play_volume = play_volume
        self.song_index = song_index
        self.queue = queue
        # self.objects.append(self)
        self.filepath = filepath
        self.n_seconds_changed = 1

        # currently pressed virtual keys (vks)
        self.current_vks = set()

        self.combination_to_function = {
            frozenset([KeyCode(vk=164), KeyCode(vk=80)]): self.pause_unpause,    # alt_l + p
            frozenset([KeyCode(vk=164), KeyCode(vk=189)]): self.decrease_volume, # alt_l + -
            frozenset([KeyCode(vk=164), KeyCode(vk=187)]): self.increase_volume, # alt_l + =
            frozenset([KeyCode(vk=164), KeyCode(vk=35)]): self.exit_app,         # alt_l + end
            frozenset([KeyCode(vk=164), KeyCode(vk=82)]): self.replay_song,      # alt_l + r
            frozenset([KeyCode(vk=164), KeyCode(vk=57)]): self.decrease_song,    # alt_l + 9
            frozenset([KeyCode(vk=164), KeyCode(vk=48)]): self.increase_song,    # alt_l + 0
            frozenset([KeyCode(vk=164), KeyCode(vk=190)]): self.next_song,       # alt_l + .
            frozenset([KeyCode(vk=164), KeyCode(vk=188)]): self.previous_song,   # alt_l + ,
            frozenset([KeyCode(vk=164), KeyCode(vk=162)]): self.shuffle_songs,   # alt_l + shift_r
            frozenset([KeyCode(vk=164), KeyCode(vk=161)]): self.gui_dl,          # alt_l + shift_r
        }


        def run_listener():
            with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                mixer.init()
                mixer.music.load(self.filepath)
                mixer.music.set_volume(self.play_volume)
                mixer.music.play()
                

                listener.join()
        run_listener()
        

    @staticmethod
    def check_song_end():
        return mixer.music.get_busy()
    

    def gui_dl(self):
        self.queue.put('gui-ydl')


    @staticmethod
    def set_volume(volume):
        mixer.music.set_volume(volume)

        
    @staticmethod
    def pause():
        mixer.music.pause() 


    @staticmethod
    def unpause():
        mixer.music.unpause() 


    def decrease_song(self):
        # if busy, set queue message to update time and slider_label in GUI 
        if mixer.music.get_busy():
            self.queue.put(f"seconds changed: {-self.n_seconds_changed}")
            Player.time_memory -= self.n_seconds_changed * 1000
            mixer.music.set_pos((Player.time_memory + mixer.music.get_pos() + Player.time_start * 1000)/1000)


    def increase_song(self):
        # if busy, set queue message to update time and slider_label in GUI 
        if mixer.music.get_busy():
            self.queue.put(f"seconds changed: {self.n_seconds_changed}")
            Player.time_memory += self.n_seconds_changed * 1000
            mixer.music.set_pos((Player.time_memory + mixer.music.get_pos() + Player.time_start * 1000)/1000)

    @staticmethod
    def load_song(filepath, start = 0):
        # reset time_memory if song is completely started over 
        if start == 0: 
            Player.time_memory = 0
        # get time memory from GUI reset_song call
        Player.time_start = start 
        # reset song load and play at specified start from GUI reset_song call
        mixer.music.load(filepath)
        mixer.music.play(start = start)

    def exit_app(self):
        self.queue.put("exit-app")


    def decrease_volume(self):
        mixer.music.set_volume(mixer.music.get_volume()-0.05)
        print("volume:", mixer.music.get_volume())
        self.queue.put("volume:", mixer.music.get_volume())


    def increase_volume(self):
        mixer.music.set_volume(mixer.music.get_volume()+0.05)
        print("volume:", mixer.music.get_volume())
        self.queue.put("volume:", mixer.music.get_volume())


    def pause_unpause(self):
        self.queue.put("pause-unpause")


    def replay_song(self):
        self.queue.put("replay-song")


    def next_song(self):
        self.queue.pot("next-song")


    def previous_song(self):
        self.queue.put("previous-song")


    def shuffle_songs(self):
        self.queue.put("shuffle-playlist") 


    def get_vk(self, key):
        """
        Get the virtual key code from a key.
        These are used so case/shift modifications are ignored.
        """
        return key.vk if hasattr(key, 'vk') else key.value.vk


    def is_combination_pressed(self, combination):
        """ Check if a combination is satisfied using the keys pressed in current_vks """
        return all([self.get_vk(key) in self.current_vks for key in combination])


    def on_press(self, key):
        """ When a key is pressed """
        vk = self.get_vk(key)  # Get the key's vk
        # print(key, vk)
        self.current_vks.add(vk)  # Add it to the set of currently pressed keys

        for combination in self.combination_to_function:  # Loop through each combination
            if self.is_combination_pressed(combination):  # Check if all keys in the combination are pressed
                self.combination_to_function[combination]()  # If so, execute the function


    def on_release(self, key):
        """ When a key is released """
        vk = self.get_vk(key)  # Get the key's vk
        # print(key, vk)
        try:
            self.current_vks.remove(vk)  # Remove it from the set of currently pressed keys
        except KeyError:
            pass