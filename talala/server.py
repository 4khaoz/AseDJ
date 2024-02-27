from typing import Union

import asyncio
import os.path

import talala.yt_utils
from talala.db import DB
from talala.music_queue import MusicQueue
from talala.playlist import Playlist
from talala.playlist import Video

track_download_dir: str = "./data/tracks"


class AddTrackError(Exception):
    pass


class Server:

    def __init__(self):
        self.db = None
        self.event_loop: asyncio.AbstractEventLoop = None
        self.playlist: Playlist = None
        self.music_queue: MusicQueue = None

    async def start(self, event_loop: asyncio.AbstractEventLoop):
        self.db = self.__setup_db()
        self.event_loop = event_loop
        self.playlist = self.db.load_playlist()
        self.music_queue = MusicQueue(self.playlist)

    async def add_track(self, track: Union[Video, str]) -> Video:
        """Adds the track to the playlist."""
        if isinstance(track, str):
            try:
                track = talala.yt_utils.get_video_data_with_ytdl(track)
            except talala.yt_utils.YTLookupError as error:
                raise AddTrackError("video not found") from error
            except talala.yt_utils.DurationPolicyError as error:
                raise AddTrackError("video is too long") from error

        if self.playlist.item_exists(track):
            raise AddTrackError("video already in playlist")

        talala.yt_utils.download_video(track.url, out_dir=track_download_dir)

        self.playlist.add_item(track)
        self.music_queue.enqueue_item(track)

        return track

    def next_track(self) -> tuple[Video, str]:
        """Retrieves the next track in the queue."""
        track = self.music_queue.dequeue_item()
        return (track, os.path.join(track_download_dir, f"{track.youtube_id}.flac"))

    def __setup_db(self) -> DB:
        db = DB()
        db.load_schema()
        return db
