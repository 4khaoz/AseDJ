#!/usr/bin/env python3

from threading import Thread
from discord.ext import commands
import discord
from yt_dlp import YoutubeDL
import json
import os
from dotenv import load_dotenv
import vlc

from talala.playlist import Playlist


load_dotenv()

# Bot Instance
bot = commands.Bot(
    command_prefix=os.getenv('COMMAND_PREFIX', default='$')
)

# Variables
playlist:       Playlist            = None 
media_player:   vlc.MediaPlayer     = None 
event_manager:  vlc.EventManager    = None
text_channel: discord.abc.GuildChannel = None
voice_channel: discord.VoiceChannel = None
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
    global playlist

    # Get text channel for event logging
    event_channel_id = os.getenv('CHANNEL')
    if event_channel_id:
        text_channel = bot.get_channel(int(event_channel_id))
    else:
        print("Will not output events on Discord. No text channel ID specified.")
    
    # Get voice channel for music streaming
    voice_channel_id = os.getenv('VOICE')
    if voice_channel_id:
        voice_channel = bot.get_channel(int(voice_channel_id))
    else:
        print("Will not stream music on Discord. No voice channel ID specified.")
    
    __setup_media_player()
    await __setup_voice_client()

    playlist = Playlist.load('playlist.json')
    await playNext()


#
# Bot Commands
#
@bot.command()
async def add(ctx: commands.Context, *arg: str):
    """
    Add video to playlist
    @param      ctx     Discord Text-Channel in which command was used
    @param      arg     Youtube-Link or Title (YT searches automatically and returns first video found)
    """
    video_data = __get_video_data_with_ytdl(arg)

    global playlist
    if playlist.item_exists(video_title=video_data['title']):
        await ctx.send("Video is already in playlist")
        return

    playlist.add_item(video_data)
    playlist.save()

    # Send Embed    
    embed = discord.Embed(
        title=f"Added {video_data['title']} to playlist",
        description=f"{video_data['url']}"
    )
    embed.set_thumbnail(url=video_data['thumbnail'])
    await ctx.send(embed=embed)

@bot.command()
async def play(ctx: commands.Context):
    """
    Manual play command
    """
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


@bot.command()
async def calibrate(ctx: commands.Context):
    thread = Thread(target=calibrate_task)
    await ctx.send("Starting Calibration...")
    thread.start()
    await ctx.send("Calibrating...")
    thread.join()
    await ctx.send("Finished Calibration")


def calibrate_task():
    i = 0
    length = len(playlist.items)

    imported_playlist = []

    for video in playlist.items:
        print(f"Calibrating... {i} / {length}")
        video_data = __get_video_data_with_ytdl(video['url'])

        imported_playlist.append(video_data)
        i += 1
    
    with open('new_playlist.json', 'w') as file:
        json.dump(imported_playlist, file, indent=4)

async def __setup_voice_client():
    """
    Connect Bot to music voice channel
    """
    global voice_client
    global voice_channel
    
    if voice_channel is None:
        return

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


async def playNext(video: dict = None):
    """
    Plays the next video
    @param      video       If video is not given, get a random one
    """
    __preload_videos(video)

    if current_video['url'].startswith('//'):
        current_video['url'] = "https:" + current_video['url']

    # Send Embed    
    if text_channel:
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

    if voice_client:
        voice_client.play(
            discord.FFmpegPCMAudio(media, **FFMPEG_OPTS),
            after=lambda e: print("Voice Client finished playing song")
        )
        voice_client.source = discord.PCMVolumeTransformer(voice_client.source, volume=0.5)

    # It'll interrupt the currently playing music
    media_player.set_mrl(media)
    media_player.play()


def __preload_videos(video: dict = None):
    global playlist
    global current_video
    global current_source
    global next_video
    global next_source

    if next_video:
        current_video = next_video
        current_source = next_source
    else:
        current_video = video if video else playlist.get_random_item()     # Python conditional operator
        current_source = __get_source_from_url(current_video['url'])

    bot.loop.create_task(__preload_next_video())


async def __preload_next_video():
    global playlist
    global next_video
    global next_source

    next_video = playlist.get_random_item()
    next_source = __get_source_from_url(next_video['url'])


def __video_finished(event):
    print(f"Finished {event}")
    
    bot.loop.create_task(playNext())


def __get_source_from_url(url: str):
    """
    Retrieves the audio source from Youtube URL with yt-dl
    @param  url     Youtube-URL to video
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
            info = ydl.extract_info(url, download=False)
        except:
            print("Extracting Information failed")

    return info['url']


def __get_video_data_with_ytdl(*arg: str) -> dict:
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

    return {
        "id": info['id'],
        "title": info['title'],
        "url": f"https://www.youtube.com/watch?v={info['id']}",
        "thumbnail": info['thumbnail']
    }

# Start bot
try:
    bot.run(os.getenv('TOKEN'), bot=True)
finally:
    # Close the VLC media player
    print("Cleaning up...")    

    if media_player:
        media_player.release()
