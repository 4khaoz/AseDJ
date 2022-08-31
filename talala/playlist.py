from __future__ import annotations

import json

import dataclasses
from dataclasses import dataclass

@dataclass
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
                # TODO: This will crash if an items has attributes that are not recogniszd by the Video dataclass
                deserialized_items = [Video(id=item.get('id'), title=item.get('title'), url=item.get('url'), thumbnail=item.get('thumbnail')) for item in json.load(file)]
                return Playlist(path=path, items=deserialized_items)

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


    def item_exists(self, item: Video) -> bool:
        """
        Get random item from playlist
        @param video The video to check against the videos in the playlist
        """
        return item in self.items


    def save(self) -> None:
        """
        Save playlist-data to JSON-File
        """
        # Don't put this inside the with statement. If any error occurs, the playlist file will be empty.
        # TODO: Write to a temporary file first?
        serialized_items = [dataclasses.asdict(item) for item in self.items]
        with open(self.path, 'w') as file:
            json.dump(serialized_items, file, indent=4)