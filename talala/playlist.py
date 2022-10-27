from __future__ import annotations
from typing import Optional

import json

import dataclasses
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Video:
    id: str
    title: str
    url: str
    thumbnail: str
    duration: int
    last_played_at: Optional[datetime] = None

    def mark_as_played(self):
        """"""
        self.last_played_at = datetime.now()


class Playlist:

    @classmethod
    def load(cls, path: str) -> Playlist:
        """
        Load playlist-data from JSON-File
        """

        # Attempts to parse the string as a ISO formatted date.
        def __parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
            if not date_string:
                return None
            return datetime.fromisoformat(date_string)

        with open(path) as file:
            try:
                print("Playlist loaded from {}".format(path))
                # TODO: This will crash if an items has attributes that are not recogniszd by the Video dataclass
                deserialized_items = [Video(id=item.get('id'), title=item.get('title'), url=item.get('url'),
                                            thumbnail=item.get('thumbnail'), duration=item.get('duration'),
                                            last_played_at=__parse_datetime(item.get('last_played_at'))) for item in
                                      json.load(file)]
                return Playlist(path=path, items=deserialized_items)

            except json.JSONDecodeError:
                print("Playlist could not be loaded")
                return Playlist(path=path)

    def __init__(self, path: str, items: Optional[list[Video]]) -> None:
        self.path: str = path
        self.items: list[Video] = items  # Static List where newly added videos are appended

    def add_item(self, item: Video) -> None:
        """
        Add video to the playlist
        @param item Video data
        """
        self.items.append(item)

    def item_exists(self, item: Video) -> bool:
        """
        Get random item from playlist
        @param item The video to check against the videos in the playlist
        """
        return item in self.items

    def item_weights(self) -> list[float]:
        now = datetime.now()

        unmapped_weights: list[int] = [(now - item.last_played_at).total_seconds() if item.last_played_at is not None else 0 for item in self.items]

        old_max = max(unmapped_weights)
        old_min = min(unmapped_weights)
        old_range = old_max - old_min
        new_min = 0.1
        new_max = 1.0
        new_range = new_max - new_min

        return [(((old_weight - old_min) * new_range) / old_range + new_min) if old_range > 0 else 0.1 for old_weight in unmapped_weights]

    def save(self) -> None:
        """
        Save playlist-data to JSON-File
        """
        # Don't put this inside the with statement. If any error occurs, the playlist file will be empty.
        # TODO: Write to a temporary file first?
        serialized_items = [dataclasses.asdict(item) for item in self.items]

        # Serialization default for unserializable objects.
        def __serialize_default(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError('Not sure how to serialize %s' % (obj,))

        with open(self.path, 'w') as file:
            json.dump(serialized_items, file, indent=4, default=__serialize_default)