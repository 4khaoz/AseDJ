import json
from talala import yt_utils
from talala.playlist import Playlist
import dataclasses

if __name__ == "__main__":
    print("Starting Calibration...")

    playlist = Playlist.load('playlist.json')

    i = 0
    length = len(playlist.items)

    imported_playlist = []
    failed_to_import = []

    for video in playlist.items:
        print(f"Calibrating... {i} / {length}")

        url = video.url
        if url.startswith('//'):
            url = f"https:{url}"

        video_data, info = yt_utils.get_video_data_with_ytdl(url)

        if video_data is None:
            failed_to_import.append(info)
        else:
            imported_playlist.append(dataclasses.asdict(video_data))
        i += 1

    with open('new_playlist.json', 'w') as file:
        json.dump(imported_playlist, file, indent=4)

    with open('failed_to_import.json', 'w') as file:
        json.dump(failed_to_import, file, indent=4)

    print("Finished Calibration")