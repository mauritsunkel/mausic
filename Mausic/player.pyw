import glob
import random
import os
from threading import Thread, Lock
from gui import UserInterface

from pygame import mixer, time
from pynput.keyboard import Key, KeyCode, Listener


class Player():
    forward_n = 0
    backward_n = 0
    amount_n = 5000

    def __init__(self, play_volume, song_index, queue):
        self.play_volume = play_volume
        self.song_index = song_index
        self.queue = queue

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
            frozenset([KeyCode(vk=164), KeyCode(vk=161)]): self.shuffle_songs,   # alt_l + shift_r
            frozenset([KeyCode(vk=164), KeyCode(vk=161)]): self.gui_dl,   # alt_l + shift_r
            
        }

        # TODO glob --> pathlib
        self.filepaths = glob.glob("testdl/*")

        def run_listener():
            with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                mixer.init()
                mixer.music.load(self.filepaths[self.song_index])
                mixer.music.set_volume(self.play_volume)
                mixer.music.play()

                listener.join()

        run_listener()
        # music_player_T = Thread(target=run_listener, daemon = True)
        # music_player_T.start()

    def gui_dl(self):
        self.queue.put('gui-ydl')

    def exit_app(self):
        exit()

    def decrease_volume(self):
        mixer.music.set_volume(mixer.music.get_volume()-0.05)
        print("volume:", mixer.music.get_volume())

    def increase_volume(self):
        mixer.music.set_volume(mixer.music.get_volume()+0.05)
        print("volume:", mixer.music.get_volume())

    def pause_unpause(self):
        mixer.music.pause() if mixer.music.get_volume() > 0 else mixer.music.unpause()
        mixer.music.set_volume(0) if mixer.music.get_volume() > 0 else mixer.music.set_volume(self.play_volume)

    def replay_song(self):
        mixer.music.rewind()
        
    def decrease_song(self):
        Player.backward_n += 1
        mixer.music.set_pos((mixer.music.get_pos()-Player.amount_n+(Player.amount_n*Player.forward_n)-(Player.amount_n*Player.backward_n))/1000)

    def increase_song(self):
        self.check_next_song()
        Player.forward_n += 1
        mixer.music.set_pos((mixer.music.get_pos()+Player.amount_n+(Player.amount_n*Player.forward_n)-(Player.amount_n*Player.backward_n))/1000)

    def next_song(self):
        Player.forward_n, Player.backward_n = 0, 0
        self.song_index = min(len(self.filepaths)-1, self.song_index + 1)
        mixer.music.load(self.filepaths[self.song_index])
        mixer.music.play()

    def previous_song(self):
        Player.forward_n, Player.backward_n = 0, 0
        self.song_index = max(0, self.song_index - 1)
        mixer.music.load(self.filepaths[self.song_index])
        mixer.music.play()

    def shuffle_songs(self):
        random.shuffle(self.filepaths)




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
        print(key, vk)
        self.current_vks.add(vk)  # Add it to the set of currently pressed keys

        for combination in self.combination_to_function:  # Loop through each combination
            if self.is_combination_pressed(combination):  # Check if all keys in the combination are pressed
                self.combination_to_function[combination]()  # If so, execute the function
            else:
                self.check_next_song()

    def on_release(self, key):
        """ When a key is released """
        vk = self.get_vk(key)  # Get the key's vk
        print(key, vk)
        self.current_vks.remove(vk)  # Remove it from the set of currently pressed keys

    def check_next_song(self):
        if mixer.music.get_busy() == False:
            self.next_song() 