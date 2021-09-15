# from os import path
from pathlib import Path 
from pydub import AudioSegment
from utils.get_bpm import beats_per_minute


# files
src = "C:\\Users\\mauri\\Desktop\\M\\Mausic\\music\\3nlSDxvt6JU.mp3"
# dst = "C:\\Users\\mauri\\Desktop\\M\\Mausic\\music\\test.wav"
# convert wav to mp3                                                            
sound = AudioSegment.from_mp3(src)
# sound.export(dst, format="wav")
# calculate BPM 
bpm = beats_per_minute(filename = sound).bpm
print(bpm)
# remove temporary .wav file after having calculated BPM
# Path(dst).unlink()