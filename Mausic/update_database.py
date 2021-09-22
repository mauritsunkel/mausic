import pandas as pd 
import glob
import eyed3
import ctypes
import numpy as np

from datetime import datetime
from utils.get_bpm import beats_per_minute
from utils.top_level_locator import top_level_path
from pathlib import Path
from collections import Counter
from pathlib import Path 
from pydub import AudioSegment

class MusicDatabase:
    objects = []
    def __init__(self):
        self.database_path = Path(top_level_path() / 'data' / 'music_database.json')
        self.rating = 75
        self.sophisticated = 50
        MusicDatabase.objects.append(self)
        self.db = self.load_database(self.database_path)


    def load_database(self, database_path):
        return pd.read_json(database_path)


    def save_database(self, mdb):
        mdb.to_json(self.database_path)


    def save_playlist_database(self, mdb, playlist_name):
        filepath = self.database_path.parent / f'playlists/{playlist_name + ".json"}'
        if filepath.is_file(): 
            return False
        else:
            mdb.to_json(filepath)
            return True


    def update_value(self, col, old_val, new_val): # self.Mbox('Messagebox', 'Song already in database.', 0)
        print(10)
        if isinstance(old_val, int) and isinstance(new_val, int):
            return new_val
        if not isinstance(new_val, int) and isinstance(old_val, int):
            self.Mbox('Messagebox', f'In column: {col}, trying to replace old int value: {old_val}, with new string value: {new_val}', 0)
        if not isinstance(old_val, int) and isinstance(new_val, int):
            self.Mbox('Messagebox', f'In column: {col}, trying to replace old str value: {old_val}, with new int value: {new_val}', 0)
        print(11)
        if isinstance(old_val, str) and isinstance(new_val, str):
            return new_val
        print(12)
        if isinstance(old_val, str) and isinstance(new_val, list):
            if old_val not in new_val:
                return new_val.append(old_val)
        print(13)
        if isinstance(old_val, list) and isinstance(new_val, str):
            if new_val not in old_val:
                return old_val.append(new_val)
        print(15)
        if isinstance(old_val, list) and isinstance(new_val, list):
            if col == 'artist':
                print(16)
                return new_val
            return list(set().union(old_val, new_val))
        print(17)


    def raw_to_formatted_metadata(self, meta):
        filename = meta['title'] 
        meta['title'] = meta['title'].lower()

        # process [] () in title       
        edges = [('[',']'), ('(',')')]
        annotations = ["Single", "EP", "Cover", "Remix", "Mashup"]
        feats = [' feat. ', ' feat ', ' ft. ', ' ft ']
        # process feat - END in title
        feat_ends = [' - ', ' | ', '!'] 
        feat_seps = [' & ', ' + ', ' en ']
        artists = []
        loops = 0
        song_type = 'Single'
        featuring = None
        # PROCESS ALL EDGES TO MAKE TITLE EASIER TO PARSE
        for edge in edges:
            if Counter(meta['title'])[edge[0]] == Counter(meta['title'])[edge[1]]:
                loops += Counter(meta['title'])[edge[0]]
            for _ in range(max(1, loops)):
                if edge[0] in meta['title'] and edge[1] in meta['title']:
                    i1 = meta['title'].find(edge[0])
                    i2 = meta['title'].find(edge[1]) + 1
                    before = meta['title'][:i1].strip()
                    between = meta['title'][i1:i2]
                    after = meta['title'][i2:]

                    for anno in annotations:
                        if anno in between:
                            song_annotation = between
                            song_type = anno
                            print(song_type)
                    for feat in feats:
                        if feat in between:
                            artist_annotation = between # TODO handle individual artists when feat found inside of edges
                    meta['title'] = before + after

                    # CHECK IF ANY FEATURINGS IN EDGES AND PROCESS ARTISTS HERE
                    
                    if any(feat in f' {between[1:len(between)-1]} ' for feat in feats):
                        featuring = f' {between[1:len(between)-1]} '
                    for end in feat_ends:
                        if meta['title'][:len(end)] == end:
                            meta['title'] = meta['title'][len(end):]
                        if meta['title'][len(end):] == end:
                            meta['title'] = meta['title'][:len(end)]

        for feat in feats:
            if feat in meta['title']:
                i1 = meta['title'].find(feat)
                i1_feat = i1 + len(feat)

                for end in feat_ends:
                    if end in meta['title'][i1_feat:]:
                        i2 = meta['title'][i1_feat:].find(end)
                        i2_end = i2 + len(end)
                        if end == ' - ':
                            i2_end = i2
                        break
                    else:
                        i2 = len(meta['title'])
                        i2_end = len(meta['title'])
                
                between = meta['title'][i1_feat:i1_feat + i2]
                before = meta['title'][:i1].strip()
                after = meta['title'][i1_feat:][i2_end:len(meta['title'])]

                for sep in feat_seps:
                    if sep in between:
                        for artist in between.split(sep):
                            artists.append(artist.strip())
                if not any([sep in between for sep in feat_seps]):
                    artists.append(between)

                meta['title'] = before + after
            
            if featuring != None and feat in featuring:
                i1 = featuring.find(feat)
                i1_feat = i1 + len(feat)
                i2_end = len(featuring)
                between = featuring[i1_feat:i1_feat + i2]
                # NOTE here go for sep in seps loop if sep found with feat inside () [] - i.e. multiple artists inside edge with seps 
                artists.append(between.strip().title())

        seps = [' - ', ' – ', ': ', ' & ', ' x ', ' by ']
        for sep in seps:
            if sep in meta['title']:
                artist = meta['title'].split(sep)[0]
                for sep2 in seps:
                    if sep2 in artist:
                        artists.append(artist.split(sep2)[1])
                        artist = artist.split(sep2)[0]
                try:
                    artist += ' ' + artist_annotation
                except NameError:
                    pass 
                artists.insert(0, artist) # insert main artist to artists on first pos 
                song = meta['title'].split(sep)[1]
                break
            else:
                if not any(sep in meta['title'] for sep in seps):
                    artist = meta['title']
                    try:
                        artist += ' ' + artist_annotation
                    except NameError:
                        pass 
                    artists.insert(0, artist)
                    song = meta['title']
                    break

        artists_titles = []
        for artist in artists:
            artists_titles.append(artist.title())

        try:
            if song.startswith('"') and song.endswith('"'):
                song = song[1:len(song)-1]
            song += ' ' + song_annotation
            song_annotation = ''
        except NameError:
            pass

        print('filename:', filename)
        print('original:', filename.title())
        print('Parsed title:', meta['title'].title())
        print('song:', song.title())
        print('artist(s):', *artists_titles, sep = ", ") 
        print('\n')

        pre_dl_meta = {
            'type': song_type,
            'rating': 75,
            'sophisticated': 50,

            'vocal': None,
            'language': None,
            'instrument': None,
            'genre': None,
            'emotion': None,
            'bpm': None,
            'rationale': None}

        new_meta = {
            'title': meta['title'],
            'song': song.title(), 
            'artist': artists_titles, 
            'filepath': meta['filepath'],
            'duration': meta['duration'], 
            'album': meta['album'], 
            'year_added': int(f'{datetime.today().year}0{datetime.today().month}{datetime.today().day}') if len(str(datetime.today().month)) == 1 else int(f'{datetime.today().year}{datetime.today().month}{datetime.today().day}'), 
            'release_year': int(meta['upload_date'][0:4]),
            'youtube_url': meta['webpage_url'],
            'tree_iid': meta['tree_iid'],

            
            **pre_dl_meta}

        return new_meta


    def metadata_to_database(self, meta, json):
        # url is better unique ID then filename or filepath (music/youtubeID.mp3, because what if youtube makes a change)
        url = meta['youtube_url']
        dropped = False
        db = json

        # check if song in database
        if url in list(db['youtube_url']):
            # row_index = list(db['youtube_url']).index(url) # DEPRECATE
            row_index = db.youtube_url[db.youtube_url == url].index[0]
            for col in db.columns:
                old_value = db.at[row_index, col]

                # DEVNOTE: SET COLNAME FOR TESTING PURPOSES
                colname = 'rating'
                if col == colname: # TODO remove only this line after testing
                    print('col:', col, '- row:', row_index, '- old_value:', old_value, '- new_value:', meta[col])
                
                try:
                    if not pd.isna(old_value).all() and old_value != [] and meta[col] == None:
                        meta[col] = old_value # if old value is something, and new_value is nothing - keep old_value 
                        if col == colname:
                            print(1)
                    elif not pd.isna(old_value).all() and old_value != [] and meta[col] != None:
                        # if old and new values are something, check if same 
                        if col == colname:
                            print(2)
                        if old_value != meta[col]:
                            meta[col] = self.update_value(col, old_value, meta[col])
                            if col == colname:
                                print(3)
                except AttributeError:
                    if col == colname:
                        print(4)
                    if not pd.isna(old_value) and old_value != [] and meta[col] == None:
                        if col == colname:
                            print(5)
                        meta[col] = old_value # if old value is something, and new_value is nothing - keep old_value 
                    elif not pd.isna(old_value) and old_value != [] and meta[col] != None:
                        # if old and new values are something, check if same 
                        if col == colname:
                            print(6)
                        if old_value != meta[col]:
                            if col == colname:
                                print(7)
                            meta[col] = self.update_value(col, old_value, meta[col])
                    if col == colname:
                        print(8)
                            
            # drop old row 
            db = db.drop([row_index])
            dropped = True
    
        if meta['bpm'] == None:
            # destination for temporary .wav file to enable BPM calculation 
            dst = "test.wav"
            # convert wav to mp3                                                            
            sound = AudioSegment.from_mp3(str(meta['filepath']))
            sound.export(dst, format="wav")
            # calculate BPM 
            meta['bpm'] = beats_per_minute(filename = dst).bpm
            # remove temporary .wav file after having calculated BPM
            Path(dst).unlink()

        # set new/updated row 
        if meta['tree_iid'] != None:
            iid = int(meta['tree_iid'])
            del meta['tree_iid']
            db.loc[iid] = pd.Series(meta) 
            print("Updated row in JSON MDB\n", db.loc[iid])
        else:
            db = db.append(meta, ignore_index = True) 
            print("New row in JSON MDB\n", db.loc[db.index[-1]])

        self.save_database(db)
        self.db = db
        return dropped


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
