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
media_player:   vlc.MediaPlayer     = None 
event_manager:  vlc.EventManager    = None
text_channel: discord.abc.GuildChannel = None
voice_channel: discord.abc.GuildChannel = None
voice_client: discord.VoiceClient = None

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

    global text_channel
    global voice_channel
    text_channel = bot.get_channel(int(os.getenv('CHANNEL')))
    voice_channel = bot.get_channel(int(os.getenv('VOICE')))
    
    __setup_media_player()
    await __setup_voice_client()

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

    await playNext()


@bot.command()
async def stop(ctx: commands.Context):
    """
    Manual stop command
    """
    global media_player
    global voice_client
    media_player.stop()
    voice_client.stop()


@bot.command()
async def volume(ctx: commands.Context, value: int):
    if value > 100:
        value = 100
    if value < 0:
        value = 0
    media_player.audio_set_volume(value)


async def __setup_voice_client():
    """
    Connect Bot to music voice channel
    """
    global voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()

    # Already connected and in the right channel
    if voice_client.channel == voice_channel and voice_client.is_connected():
        return

    # Move Voice
    if voice_client.is_connected():
        await voice_client.move_to(voice_channel)


def __setup_media_player():
    """
    Setup a new VLC media player instance and event manager
    """    
    global media_player
    global event_manager
    
    media_player    = vlc.MediaPlayer() 
    event_manager   = media_player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, __video_finished)


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

    if current_video['url'].startswith('//'):
        current_video['url'] = "https:" + current_video['url']

    # Send Embed    
    embed = discord.Embed(
        title=f"Now playing {current_video['title']}",
        description=f"{current_video['url']}"
    )
    embed.set_thumbnail(url=current_video['thumbnail'])
    await text_channel.send(embed=embed)

    __play(current_source)


def __play(media: str):
    """
    @param      media       Youtube Audio Source URL
    """    
    global media_player
    global event_manager
    global voice_client

    FFMPEG_OPTS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    voice_client.play(
        discord.FFmpegPCMAudio(media, **FFMPEG_OPTS),
        after=lambda e: print("Voice Client finished playing song")
    )
    voice_client.source = discord.PCMVolumeTransformer(voice_client.source, volume=0.5)

    # It'll interrupt the currently playing music
    media_player.set_mrl(media)
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
        current_video = video if video else __get_random_item()     # Python conditional operator
        current_source = __get_source_from_url(current_video['url'])

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
try:
    bot.run(os.getenv('TOKEN'), bot=True)
finally:
    # Close the VLC media player
    print("Cleaning up...")    

    if media_player is not None:
        media_player.release()