#!/usr/bin/env python3

from discord.ext import commands
import discord
from yt_dlp import YoutubeDL
import json
import os
from dotenv import load_dotenv
import vlc
import random

load_dotenv()

# Bot Instance
bot = commands.Bot(
    command_prefix='$'
)

# Variables
playlist = []
media_player = None
event_manager = None
channel = None

current_video = None
current_source = None
next_video = None
next_source = None

#
# Bot Events
#
@bot.event
async def on_ready():
    print('Logged in')

    global channel
    channel = bot.get_channel(int(os.getenv('CHANNEL')))

    __load_playlist()
    await playNext()


#
# Bot Commands
#
@bot.command()
async def add(ctx: commands.Context, arg: str):
    """
    Add video to playlist
    @param      ctx     Discord Text-Channel in which command was used
    @param      arg     Youtube-Link or Title (YT searches automatically and returns first video found)
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'no_warnings': True,
    }

    # Extract Youtube Video Data
    with YoutubeDL(ydl_opts) as ydl:
        try:
            if "https://" not in arg[0]:
                info = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
            else:
                info = ydl.extract_info(arg[0], download=False)
        except:
            print("Extracting Information failed")

    video_data = {
        "title": info['title'],
        "url": f"https://www.youtube.com/watch?v={info['id']}",
        "thumbnail": info['thumbnail']
    }

    global playlist
    playlist.append(video_data)
    __save_playlist()

@bot.command()
async def play(ctx: commands.Context, title: str = None):
    """
    Manual play command
    """
    if title:
        # TODO: find song to play by title
        #media_player.play()
        pass

    playNext()


@bot.command()
async def stop(ctx: commands.Context):
    """
    Manual stop command
    """
    global media_player
    media_player.stop()


@bot.command()
async def volume(ctx: commands.Context, value: int):
    if value > 100:
        value = 100
    if value < 0:
        value = 0
    media_player.audio_set_volume(value)


def __load_playlist():
    """
    Load playlist-data from JSON-File
    """
    global playlist

    with open('playlist.json') as file:
        try:
            playlist = json.load(file)
            print("Playlist loaded from playlist.json")
        except json.JSONDecodeError:
            print("Playlist could not be loaded")


def __save_playlist():
    """
    Save playlist-data to JSON-File
    """
    with open('playlist.json', 'w') as file:
        json.dump(playlist, file, indent=4)


async def playNext(video: dict = None):
    """
    Plays the next video
    @param      video       If video is not given, get a random one
    """
    await __preload_videos(video)

    # Send Embed
    embed = discord.Embed(
        title=f"Now playing {current_video['title']}",
        description=f"{current_video['url']}"
    )
    embed.set_thumbnail(url=current_video['thumbnail'])
    #await channel.send(embed=embed)

    __play(current_source)

def __play(media: str):
    """
    @param      media       Youtube Audio Source URL
    """
    global media_player
    global event_manager

    media_player = vlc.MediaPlayer(media)
    event_manager = media_player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, __video_finished)
    media_player.play()

async def __preload_videos(video: dict = None):
    global current_video
    global current_source
    global next_video
    global next_source

    if next_video:
        current_video = next_video
        current_source = next_source
    else:
        current_video = __get_random_item()
        current_source = __get_source_from_url(current_video['url'])

    if video:
        current_video = video
        current_source = __get_source_from_url(video['url'])

    next_video = __get_random_item()
    next_source = __get_source_from_url(next_video['url'])


def __video_finished(event):
    print(f"Finished {event}")
    
    bot.loop.create_task(playNext())


def __get_random_item():
    global playlist

    if playlist:
        return random.choice(playlist)
    return None


def __get_source_from_url(url: str):
    """
    Retrieves the audio source from Youtube URL with yt-dl
    @param  url     Youtube-URL to video
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        # 'postprocessors': [{
        #     'key': 'FFmpegExtractAudio',
        #     'preferredcodec': 'mp3',
        #     'preferredquality': '192',
        # }],
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'no_warnings': True,
    }

    # Extract Youtube Video Data
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except:
            print("Extracting Information failed")

    return info['url']


# Start bot
bot.run(os.getenv('TOKEN'), bot=True)