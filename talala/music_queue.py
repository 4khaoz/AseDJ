import random

import asyncio

from talala import yt_utils
from talala.playlist import Playlist

class MusicQueue:

    def __init__(self, playlist: Playlist, event_loop: asyncio.AbstractEventLoop) -> None:
        self.playlist = playlist
        self.event_loop = event_loop

        self.current_video: dict = None
        self.current_source: dict = None

        self.next_video: dict = None
        self.next_source: dict = None

        self.__queue: list[dict] = None     # Shuffled list to play


    def enqueue_item(self, item: dict) -> None:
        if self.__queue is None:
            self.__queue = [item]
        else:
            self.__queue.insert(0, item)


    def dequeue_item(self) -> dict:
        """
        Dequeues the next item in queue
        """

        if not self.__queue:
            self.__load_queue()
        return self.__queue.pop(0)


    def next_item(self, video: dict = None) -> dict:
        if video:
            self.current_video = video
            self.current_source = yt_utils.get_source_from_url(self.current_video['url'])
        elif self.next_video:
            self.current_video = self.next_video
            self.current_source = self.next_source
        else:
            self.current_video = self.dequeue_item()     # Python conditional operator
            self.current_source = yt_utils.get_source_from_url(self.current_video['url'])

        self.event_loop.create_task(self.__preload_next_video())

        return (self.current_video, self.current_source)


    async def __preload_next_video(self):
        self.next_video = self.dequeue_item()
        self.next_source = yt_utils.get_source_from_url(self.next_video['url'])


    def __load_queue(self) -> None:
        self.__queue = random.sample(self.playlist.items, len(self.playlist.items))
        print("Shuffling queue")