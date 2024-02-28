from yt_dlp import YoutubeDL
import validators

from talala.playlist import Video

# 12-min Policy
MAX_DURATION = 720


class YTLookupError(Exception):
    """Exception raised when unable to lookup video"""

    def __init__(self, *args, url: str):
        self.url = url
        super().__init__(*args)


class DurationPolicyError(Exception):
    """Exception raised when Video-Duration-Policy is violated"""

    def __init__(self, *args, url: str):
        self.url = url
        super().__init__(*args)


def get_video_data_with_ytdl(query: str) -> Video:
    ydl_opts = {
        "format": "bestaudio/best",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "no_warnings": True,
    }

    # Extract Youtube Video Data
    with YoutubeDL(ydl_opts) as ydl:
        try:
            if validators.url(query):
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][
                    0
                ]
        except Exception as err:
            raise YTLookupError(
                f"Extracting Information failed: {err}", url=query
            ) from err

    if info["duration"] > MAX_DURATION:
        # Video Duration violates the 12min-limit-policy
        raise DurationPolicyError(f"Video-Duration-Policy violated", url=query)

    return Video(
        youtube_id=info["id"],
        title=info["title"],
        url=f"https://www.youtube.com/watch?v={info['id']}",
        thumbnail_url=info["thumbnail"],
        duration=info["duration"],
    )


def download_audio(url: str, out_dir: str):
    with downloader(out_dir=out_dir) as ytd:
        ytd.download(url)


def downloader(out_dir: str) -> YoutubeDL:
    ydl_opts = {
        "noplaylist": True,
        "restrictfilenames": True,
        "format": "bestaudio/best",
        "ignoreerrors": False,
        "paths": {"home": out_dir},
        "outtmpl": "%(id)s.%(ext)s",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "flac"}],
    }

    return YoutubeDL(ydl_opts)
