import json

import os.path

from yt_dlp import DownloadError

import talala.yt_utils as yt_utils

from talala.playlist import Video
from talala.db import DB


def load_playlist_items() -> list[dict]:
    items = []
    known_ids = set()
    with open("./playlist.json", mode="r", encoding="utf8") as f:
        for item in json.load(f):
            if not item["id"]:
                continue
            if item["id"] in known_ids:
                print("duplicated key:", item["id"])
                continue
            items.append(
                Video(
                    youtube_id=item["id"],
                    url=item["url"],
                    title=item["title"],
                    duration=item["duration"],
                    thumbnail_url=item["thumbnail"],
                )
            )

    return items


def main():
    downloaded_items = []
    track_download_dir = "./data/tracks"
    with yt_utils.downloader(out_dir=track_download_dir) as ytd:
        for item in load_playlist_items():
            if os.path.exists(
                os.path.join(track_download_dir, f"{item.youtube_id}.flac")
            ):
                print("Already downloaded", item.youtube_id)
                continue
            try:
                ytd.download(item.url)
                downloaded_items.append(item)
            except DownloadError:
                print("Failed to download", item.youtube_id)
                continue

    with DB() as con:
        con.load_schema()
        con.insert_tracks(downloaded_items, skip_conflicts=True)


if __name__ == "__main__":
    main()
