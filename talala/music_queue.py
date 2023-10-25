import asyncio

from typing import Optional

from datetime import datetime

from talala import yt_utils
from talala.playlist import Playlist
from talala.playlist import Video
from talala.shuffle import weighted_shuffle


class MusicQueue:

    def __init__(self, playlist: Playlist, event_loop: asyncio.AbstractEventLoop) -> None:
        self.playlist: Playlist = playlist
        self.event_loop: asyncio.AbstractEventLoop = event_loop

        self.current_video: Optional[Video] = None
        self.current_source: Optional[str] = None

        self.next_video: Optional[Video] = None
        self.next_source: Optional[str] = None

        self.__queue: Optional[list[Video]] = None     # Shuffled list to play

    @property
    def playlist_items(self) -> list[Video]:
        return self.playlist.items

    @property
    def playlist_item_weights(self) -> list[float]:
        now = datetime.now()

        unmapped_weights: list[int] = [(now - item.last_played_at).total_seconds(
        ) if item.last_played_at is not None else 0 for item in self.playlist_items]

        old_max = max(unmapped_weights)
        old_min = min(unmapped_weights)
        old_range = old_max - old_min
        new_min = 0.1
        new_max = 1.0
        new_range = new_max - new_min

        return [(((old_weight - old_min) * new_range) / old_range + new_min) if old_range > 0 else 0.1 for old_weight in unmapped_weights]

    def enqueue_item(self, video: Video) -> None:
        if self.__queue is None:
            self.__queue = [video]
        else:
            self.__queue.insert(0, video)

    def dequeue_item(self) -> Video:
        """
        Dequeues the next item in queue
        """

        if not self.__queue:
            self.__load_queue()
        return self.__queue.pop(0)

    def next_item(self, video: Video = None) -> tuple[Video, str]:
        if video:
            self.current_video = video
            self.current_source = yt_utils.get_source_from_url(
                self.current_video.url)
        elif self.next_video:
            self.current_video = self.next_video
            self.current_source = self.next_source
        else:
            self.current_video, self.current_source = self.__load_source()

        self.event_loop.create_task(self.__preload_next_video())

        return self.current_video, self.current_source

    async def __preload_next_video(self) -> None:
        self.next_video, self.next_source = self.__load_source()

    def __load_source(self) -> Optional[tuple[Video, str]]:
        while True:
            next_item = self.dequeue_item()
            if next_item is None:
                return None
            try:
                return next_item, yt_utils.get_source_from_url(next_item.url)
            except yt_utils.YTLookupError:
                # Unable to retrieve information for this item.
                continue

    def __load_queue(self) -> None:
        print("Shuffling queue")
        self.__queue = weighted_shuffle(
            self.playlist_items, self.playlist_item_weights)
