from typing import Optional
from yt_dlp import YoutubeDL
import validators

from talala.playlist import Video

def get_video_data_with_ytdl(arg: tuple[str, ...]) -> tuple[Optional[Video], Optional[dict]]:
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
            if validators.url(arg[0]):
                info = ydl.extract_info(arg[0], download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        except Exception as e:
            print(f"Extracting Information failed: {e}")
            return (None, {"url": arg})

    video = Video(
        id=info['id'],
        title=info['title'],
        url=f"https://www.youtube.com/watch?v={info['id']}",
        thumbnail=info['thumbnail'])

    return (video, None)


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