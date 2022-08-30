from __future__ import annotations

import json

from dataclasses import dataclass

@dataclass(slots=True)
class Video:
    id: str
    title: str
    url: str
    thumbnail: str


class Playlist:

    def load(path: str) -> Playlist:
        """
        Load playlist-data from JSON-File
        """

        with open(path) as file:
            try:
                print("Playlist loaded from {}".format(path))
                return Playlist(path=path, items=[Video(**item) for item in json.load(file)])

            except json.JSONDecodeError:
                print("Playlist could not be loaded")
                return Playlist(path=path)


    def __init__(self, path: str, items: list[Video] = []) -> None:
        self.path: str          = path
        self.items: list[Video] = items    # Static List where newly added videos are appended


    def add_item(self, item: Video) -> None:
        """
        Add video to the playlist
        @param item Video data
        """
        self.items.append(item)


    def item_exists(self, video_id: str) -> bool:
        """
        Get random item from playlist
        @param video_id The ID of the video to check against the videos in the playlist
        """
        return any(video_id in video_data['id'] for video_data in self.items)


    def save(self) -> None:
        """
        Save playlist-data to JSON-File
        """
        with open(self.path, 'w') as file:
            json.dump([item.asdict() for item in self.items], file, indent=4)