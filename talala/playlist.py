from __future__ import annotations
from typing import Optional

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Video:
    youtube_id: str
    url: str
    title: str
    duration: int
    thumbnail_url: Optional[str] = None
    last_played_at: Optional[datetime] = None
    id: int = None

    def mark_as_played(self):
        self.last_played_at = datetime.now()


class Playlist:

    def __init__(self, items: Optional[list[Video]]) -> None:
        self.items: list[Video] = items

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
