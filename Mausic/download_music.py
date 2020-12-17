from __future__ import unicode_literals
import youtube_dl
import update_database as ud

# DEVNOTE: need to download & install & PATH ffmpeg: https://www.youtube.com/watch?v=r1AtmY-RMyQ

class Music_download:
	def __init__(self, youtube_link, download_wav = True, download_mp4 = False):
		self.ydl_audio_options = {
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
		'format': 'bestvideo[ext=mp4]', # can try webm extension
		# 'format': 'bestvideo[ext=mp4]+bestaudio[ext=wav]/best',
		'outtmpl': 'wav_music' + '/%(title)s.%(ext)s',
		}

		if download_mp4:
			self.download_mp4(link = youtube_link)
		if download_wav:
			self.download_wav(link = youtube_link)
		
	@staticmethod
	def download_annotations(link):
		with youtube_dl.YoutubeDL() as ydl: 
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


if __name__ == '__main__':
	
	link = 'https://www.youtube.com/watch?v=3nlSDxvt6JU'

	MD = Music_download(youtube_link = link, download_wav = True, download_mp4 = False)
	
	
	

	# link = 'https://www.youtube.com/watch?v=3nlSDxvt6JU' # song
	# link = 'https://www.youtube.com/watch?v=tqRC6A0mlk4&list=PLW8_7fTWU3uZbQk1HviUs4x9mxXmZDFUI' # album