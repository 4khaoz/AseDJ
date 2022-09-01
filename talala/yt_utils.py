from typing import Optional
from yt_dlp import YoutubeDL
import validators

from talala.playlist import Video

class YTLookupError(Exception):
    """Exception raised when unable to lookup video"""
    def __init__(self, url, *args):
        self.url = url
        super().__init__(*args)

def get_video_data_with_ytdl(query: str) -> Video:
    ydl_opts = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'no_warnings': True,
    }

    # Extract Youtube Video Data
    with YoutubeDL(ydl_opts) as ydl:
        try:
            if validators.url(query):
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        except Exception as err:
            raise YTLookupError(url=query, message=f"Extracting Information failed: {err}") from err

    return Video(
        id=info['id'],
        title=info['title'],
        url=f"https://www.youtube.com/watch?v={info['id']}",
        thumbnail=info['thumbnail'])

def get_source_from_url(url: str):
    """
    Retrieves the audio source from Youtube URL with yt-dl
    @param  url     Youtube-URL to video
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'no_warnings': True,
    }

    # Extract Youtube Video Data
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except:
            print("Extracting Information failed")

    return info['url']