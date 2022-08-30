from typing_extensions import Self

import json
import random

class Playlist:

    def load(path: str) -> Self:
        """
        Load playlist-data from JSON-File
        """

        with open(path) as file:
            try:
                print("Playlist loaded from {}".format(path))
                return Playlist(path=path, items=json.load(file))

            except json.JSONDecodeError:
                print("Playlist could not be loaded")
                return Playlist(path=path)


    def __init__(self, path: str, items: list[dict] = []) -> None:
        self.path: str           = path
        self.items: list[dict]   = items    # Static List where newly added videos are appended
        self.__queue: list[dict] = None     # Shuffled list to play


    def add_item(self, item: dict) -> None:
        """
        Add video to the playlist
        @param item Video data
        """
        self.items.append(item)

        if self.__queue is None:
            self.__queue = [item]
        else:
            self.__queue.insert(0, item)


    def item_exists(self, video_id: str) -> bool:
        """
        Get random item from playlist
        @param video_id The ID of the video to check against the videos in the playlist
        """
        return any(video_id in video_data['id'] for video_data in self.items)


    def get_random_item(self) -> dict:
        """
        Get random item from playlist
        """
        if not self.__queue:
            self.__load_queue()
        return self.__queue.pop(0)


    def save(self) -> None:
        """
        Save playlist-data to JSON-File
        """
        with open(self.path, 'w') as file:
            json.dump(self.items, file, indent=4)


    def __load_queue(self) -> None:
        self.__queue = random.sample(self.items, len(self.items))
        print("Shuffling queue")
        print(self.__queue)
