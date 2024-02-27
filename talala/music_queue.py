from typing import Optional

from datetime import datetime

from talala.playlist import Playlist
from talala.playlist import Video
from talala.shuffle import weighted_shuffle


class MusicQueue:

    def __init__(self, playlist: Playlist) -> None:
        self.playlist: Playlist = playlist
        self.__queue: Optional[list[Video]] = None  # Shuffled list to play

    @property
    def playlist_items(self) -> list[Video]:
        return self.playlist.items

    @property
    def playlist_item_weights(self) -> list[float]:
        now = datetime.now()

        unmapped_weights: list[int] = [
            (
                (now - item.last_played_at).total_seconds()
                if item.last_played_at is not None
                else 0
            )
            for item in self.playlist_items
        ]

        old_max = max(unmapped_weights)
        old_min = min(unmapped_weights)
        old_range = old_max - old_min
        new_min = 0.1
        new_max = 1.0
        new_range = new_max - new_min

        return [
            (
                (((old_weight - old_min) * new_range) / old_range + new_min)
                if old_range > 0
                else 0.1
            )
            for old_weight in unmapped_weights
        ]

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

    def __load_queue(self) -> None:
        print("Shuffling queue")
        self.__queue = weighted_shuffle(self.playlist_items, self.playlist_item_weights)
