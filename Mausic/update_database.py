import pandas as pd 
import glob
import eyed3
import ctypes
import numpy as np

from datetime import datetime
from utils.get_bpm import beats_per_minute

class Music_database:
    objects = []
    def __init__(self):
        self.database_path = 'music_database.json'
        self.rating = 75
        self.sophisticated = 50
        Music_database.objects.append(self)
        
    # def mp3_downloads_to_database(self, ):
    #     mdb = self.load_database(self.database_path)

    #     c = 0
    #     mp3s = glob.glob("music/*.mp3")
    #     for i in range(0, len(mp3s)):
    #         mp3s[i] = mp3s[i][6:-4]
    #         if mp3s[i] not in list(mdb['filepath']):
    #             c += 1
    #             mdb = self.append_mp3_to_database(mp3s[i], mdb)

    #     self.save_database()

    #     if c > 0:
    #         self.Mbox('Messagebox', 'Check the last {} rows of the music database.'.format(c), 0)
    #     else: 
    #         self.Mbox('Messagebox', 'Music database is up to date'.format(c), 0)

    def load_database(self, database_path):
        return pd.read_json(database_path)

    def save_database(self, mdb):
        mdb.to_json(self.database_path)

    def append_mp3_to_database(self, mp3, db):
        audio = eyed3.load("music/{}.mp3".format(mp3))
        album = None if audio.tag.album == None else audio.tag.album
        genre = None if audio.tag.genre == None else audio.tag.genre
        duration = None if audio.info.time_secs == None else audio.info.time_secs
        song = None if audio.tag.title == None else audio.tag.title
        artist = None if audio.tag.artist == None else audio.tag.artist
        rating = self.rating
        sophisticated = self.sophisticated
        year_added = datem = datetime.today().year
        if ' - ' in mp3:
            artist = mp3.split(' - ')[0] if audio.tag.artist == None else audio.tag.artist
            song = mp3.split(' - ')[1] if audio.tag.title == None else audio.tag.title
        filepath = mp3
            
        row = {'song': song, 'artist': artist, 'filepath': filepath, 'duration': duration, 
            'genre': genre, 'album': album, 'rating': rating, 'sophisticated': sophisticated, 'year_added': year_added}
        return db.append(row, ignore_index = True)

    def update_value(self, col, old_val, new_val): # self.Mbox('Messagebox', 'Song already in database.', 0)
        if isinstance(old_val, int) & isinstance(new_val, int):
            return new_val
        if not isinstance(new_val, int) & isinstance(old_val, int):
            self.Mbox('Messagebox', 'Trying to replace int value with string', 0)
        if not isinstance(old_val, int) & isinstance(new_val, int):
            self.Mbox('Messagebox', 'Trying to replace string value with int', 0)
        if isinstance(old_val, str) & isinstance(new_val, str):
            return new_val
        if isinstance(old_val, str) & isinstance(new_val, list):
            if old_val not in new_val:
                return new_val.append(old_val)
        if isinstance(old_val, list) & isinstance(new_val, str):
            if new_val not in old_val:
                return old_val.append(new_val)
        if isinstance(old_val, list) & isinstance(new_val, list):
            return list(set().union(old_val, new_val))

    def metadata_to_database(self, meta):
        if meta['alt_title'] != None:
            song = meta['alt_title']
        else:
            if ' - ' in meta['title']:
                song = meta['title'].split(' - ')[1]
            else: 
                song = meta['title']
        if meta['artist'] != None:
            artist = meta['artist']
        else:
            if ' - ' in meta['title']:
                artist = meta['title'].split(' - ')[0]
            else:
                artist = meta['title']
        
        filename = '{} - {}'.format(artist, song)

        # TODO try these first 
        # set pre-download annotation options in a dict and pass them to a variable called pre_dl_meta in the metadata_to_database function
        ## type 
        ## vocal
        ## language = 'english' if vocal != None else None
        ## instrument
        ## genre
        ## emotion
        ## rationale
        ## sophisticated
        ## rating
        ## 

        # remove after testing
        pre_dl_meta = {
            'type': None,
            'vocal': None,
            'language': None,
            'instrument': None,
            'genre': None,
            'emotion': None,
            'rationale': None}

        new_values = {
            'song': song, 
            'artist': artist, 
            'filepath': filename,
            'duration': meta['duration'], 
            'album': meta['album'], 
            'year_added': datetime.today().year, 
            'rating': self.rating, 
            'sophisticated': self.sophisticated, 
            'release_year': int(meta['upload_date'][0:4]),
            'youtube_url': meta['webpage_url'],
            'bpm': None,
            **pre_dl_meta}

        # check if song in database
        db = self.load_database(self.database_path)
        if filename in list(db['filepath']):
            row_index = list(db['filepath']).index(filename)
            for col in db.columns:
                old_value = db.at[row_index, col]
                print('col:', col, '- row:', row_index, '- old_value:', old_value, '- new_value:', new_values[col])
                if pd.isna(old_value):
                    continue # if old value is nothing, new_value will be added
                elif not pd.isna(old_value) and new_values[col] == None:
                    new_values[col] = old_value # if old value is something, and new_value is nothing - keep old_value 
                elif not pd.isna(old_value) and new_values[col] != None:
                    # if old and new values are something, check if same 
                    if old_value != new_values[col]:
                        new_values[col] = self.update_value(col, old_value, new_values[col]) 
            
            # drop old row 
            db = db.drop([row_index])
        else:
            # calculate and add bpm for new songs 
            new_values['bpm'] = beats_per_minute(filename = 'wav_music/{}.wav'.format(meta['title'])).bpm

        # append new/updated row 
        db = db.append(new_values, ignore_index = True)
        self.save_database(db)
    


        # TODO after download: move wav from dl folder to music folder? 

    def Mbox(self, title, text, style):
        return ctypes.windll.user32.MessageBoxW(0, text, title, style+64)
        ##  Styles:
        ##  0 : OK
        ##  1 : OK | Cancel
        ##  2 : Abort | Retry | Ignore
        ##  3 : Yes | No | Cancel
        ##  4 : Yes | No
        ##  5 : Retry | Cancel 
        ##  6 : Cancel | Try Again | Continue

        ## To also change icon, add these values to previous number
        # 16 Stop-sign icon
        # 32 Question-mark icon
        # 48 Exclamation-point icon
        # 64 Information-sign icon consisting of an 'i' in a circle

    

    # Tasty Planet	The Noisy Freaks					electronic 	2012	2020	306,2479077		gaming	50	75	The Noisy Freaks - Tasty Planet	
