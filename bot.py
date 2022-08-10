#!/usr/bin/env python3

from discord.ext import commands
import discord
import youtube_dl
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
media_player = vlc.MediaPlayer()
event_manager = media_player.event_manager()

def __video_finished():
    pass


# Events & Inits
event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, __video_finished)

@bot.event
async def on_ready():
    print('Logged in')

    __load_playlist()
    __play()


#
# Commands
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
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            if "https://" not in arg[0]:
                info = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
            else:
                info = ydl.extract_info(arg[0], download=False)
        except:
            raise youtube_dl.utils.DownloadError('RIP')

    video_data = {
        "title": info['title'],
        "source": info['formats'][0]['url'],   # Maybe not needed
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

    __play(__get_random_item())


@bot.command()
async def stop(ctx: commands.Context):
    """
    Manual stop command
    """
    pass


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


def __play(video: dict = None):
    if not video:
        return

    embed = discord.Embed(
        title=f"Now playing {video['title']}",
        description=f"{video['url']}"
    )
    embed.set_thumbnail(url=video['thumbnail'])

    #await music_channel.send(embed=embed)
    #media_player.set_media(video['source'])
    #media_player.play()
    vlc.MediaPlayer(video['source']).play()


def __get_random_item():
    global playlist

    if playlist:
        return random.choice(playlist)
    return None



# Start bot
bot.run(os.getenv('TOKEN'), bot=True)