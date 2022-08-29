import json
from talala import yt_utils
from talala.playlist import Playlist

if __name__ == "__main___":
    print("Starting Calibration...")

    playlist = Playlist.load('playlist.json')

    i = 0
    length = len(playlist.items)

    imported_playlist = []
    failed_to_import = []

    for video in playlist.items:
        print(f"Calibrating... {i} / {length}")
        video_data = yt_utils.get_video_data_with_ytdl(video['url'])

        if 'failed' in video_data:
            failed_to_import.append(video_data)
        else:
            imported_playlist.append(video_data)
        i += 1
    
    with open('new_playlist.json', 'w') as file:
        json.dump(imported_playlist, file, indent=4)

    with open('failed_to_import.json', 'w') as file:
        json.dump(failed_to_import, file, indent=4)

    print("Finished Calibration")