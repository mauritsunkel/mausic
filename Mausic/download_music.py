from __future__ import unicode_literals
import youtube_dl
import update_database as ud

# DEVNOTE: need to download & install & PATH ffmpeg: https://www.youtube.com/watch?v=r1AtmY-RMyQ

class MusicDownload:
	def __init__(self, youtube_link = '', download_wav = False, download_mp4 = False, download_mp3 = True):
		if youtube_link == "":
			return

		self.ydl_audio_options = {
			'noplaylist': True,
			'format': 'bestaudio/best',
			# 'format': 'bestvideo',
			# 'format': 'bestvideo[ext=mp4]+bestaudio[ext=wav]/best',
			'outtmpl': 'wav_music' + '/%(title)s.%(ext)s',
			'postprocessors': [{
				'key': 'FFmpegExtractAudio',
				'preferredcodec': 'wav',
				'preferredquality': '192'}],
		}
		self.ydl_video_options = {
		# 'format': 'bestaudio/best',
		'noplaylist': True,
		'format': 'bestvideo[ext=mp4]', # can try webm extension
		# 'format': 'bestvideo[ext=mp4]+bestaudio[ext=wav]/best',
		'outtmpl': 'wav_music' + '/%(title)s.%(ext)s',
		}

		if download_mp4:
			self.download_mp4(link = youtube_link)
		if download_wav:
			self.download_wav(link = youtube_link)
		if download_mp3:
			self.download_mp3(link = youtube_link)
		
		
	@staticmethod
	def download_annotations(link):
		ydl_annotation_options = {
			'noplaylist': True
		}
		with youtube_dl.YoutubeDL(ydl_annotation_options) as ydl: 
			return ydl.extract_info(link, download = False)


	def download_mp4(self, link):
		with youtube_dl.YoutubeDL(self.ydl_video_options) as ydl:
			ydl.download([link])


	def download_wav(self, link, to_database = True, download = True):
		MDB = ud.Music_database()
		with youtube_dl.YoutubeDL(self.ydl_audio_options) as ydl:
			if download:
				ydl.download([link])
			if to_database:
				info = ydl.extract_info(link, download = False)
				if 'entries' in info.keys():
					MDB.metadata_to_database(meta = info['entries'])
				else:
					MDB.metadata_to_database(meta = info)


	@staticmethod
	def download_mp3(link, to_database = True, download = True):
		# youtube_ID = raw_meta['webpage_url'].split('watch?v=')[1]
		# Path(self.music_path / str(raw_meta['title'] + '.mp3')).rename(r'{}'.format(Path(self.music_path / str(youtube_ID + '.mp3'))))
		ydl_mp3_options = {
			'noplaylist': True,
			'format': 'bestaudio/best',
			# 'format': 'bestvideo',
			# 'format': 'bestvideo[ext=mp4]+bestaudio[ext=wav]/best',
			'outtmpl': 'music' + '/%(id)s.%(ext)s',
			'postprocessors': [{
				'key': 'FFmpegExtractAudio',
				'preferredcodec': 'mp3',
				'preferredquality': '192'}],
		}
		MDB = ud.MusicDatabase()
		with youtube_dl.YoutubeDL(ydl_mp3_options) as ydl:
			return ydl.extract_info(link, download = True)