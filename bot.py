#!/usr/bin/env python3

from discord.ext import commands
import discord
import json
import os
from dotenv import load_dotenv
import vlc

from talala import yt_utils
from talala.music_queue import MusicQueue
from talala.playlist import Playlist
from talala.playlist import Video


load_dotenv()

# Bot Instance
bot = commands.Bot(
    command_prefix=os.getenv('COMMAND_PREFIX', default='$')
)

# Variables
playlist:       Playlist                    = None
music_queue:    MusicQueue                  = None
media_player:   vlc.MediaPlayer             = None
event_manager:  vlc.EventManager            = None
text_channel:   discord.abc.GuildChannel    = None
voice_channel:  discord.VoiceChannel        = None
voice_client:   discord.VoiceClient         = None

#
# Bot Events
#
@bot.event
async def on_ready():
    print('Logged in')

    global text_channel
    global voice_channel
    global playlist
    global music_queue

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
    music_queue = MusicQueue(playlist, event_loop=bot.loop)

    await playNext()


#
# Bot Commands
#
@bot.command()
async def connect(ctx: commands.Context):
    """
    Manually connect bot to voice channel if e.g. disconnected
    """
    await __setup_voice_client()

@bot.command()
async def add(ctx: commands.Context, *, query: str):
    """
    Add video to playlist
    @param      ctx     Discord Text-Channel in which command was used
    @param      query     Youtube-Link or Title (YT searches automatically and returns first video found)
    """

    message: discord.Message = await ctx.send(content=f"Searching video: <{query}>")

    try:
        video_data = yt_utils.get_video_data_with_ytdl(query)
    except yt_utils.YTLookupError:
        await message.edit(content="Failed to retrieve Video data")
        return

    global playlist
    if playlist.item_exists(video_data):
        await message.edit(content="Video is already in playlist")
        return

    print(f"Adding video: {video_data}")

    playlist.add_item(video_data)
    playlist.save()

    music_queue.enqueue_item(video_data)

    # Send Embed
    embed = discord.Embed(
        title=f"Added {video_data.title} to playlist",
        description=f"{video_data.url}"
    )
    embed.set_thumbnail(url=video_data.thumbnail)
    await message.edit(content=None, embed=embed)

#
# TODO: Cleanup and refactor mark, unmark and meme command
#

@bot.command()
async def mark(ctx: commands.Context, key: str, *arg: str):
    try:
        with open('marked.json', 'r') as file:
            marked = json.load(file)
    except:
        print("marked.json could not be loaded")
        marked = {}

    if key in marked:
        await ctx.send("Key already exists. Unmark first or use another.")
        return

    marked[key] = yt_utils.get_video_data_with_ytdl(arg)

    with open('marked.json', 'w') as file:
        json.dump(marked, file, indent=4)

    await ctx.send("Key applied")


@bot.command()
async def unmark(ctx: commands.Context, key: str):
    await ctx.send(f"The key '{key}' has been freed")

@bot.command()
async def meme(ctx: commands.Context, key: str):
    try:
        with open('marked.json', 'r') as file:
            marked = json.load(file)
    except:
        print("marked.json could not be loaded")
        return

    if key in marked:
        media_player.stop()
        voice_client.stop()
        await playNext(marked[key])
        await ctx.send("Ehehehe")
    else:
        await ctx.send("Key not found")


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


async def __setup_voice_client():
    """
    Connect Bot to music voice channel
    """
    global voice_client
    global voice_channel

    if voice_channel is None:
        return

    # Create a new voice channel if there's none or it's no longer connected
    if voice_client is None or not voice_client.is_connected():
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


async def playNext(video: Video = None):
    """
    Plays the next video
    @param      video       If video is not given, get a random one
    """

    current_video, current_source = music_queue.next_item(video)

    # Send Embed
    if text_channel:
        embed = discord.Embed(
            title=f"Now playing {current_video.title}",
            description=f"{current_video.url}"
        )
        embed.set_thumbnail(url=current_video.thumbnail)
        await text_channel.send(embed=embed)

    await __play(current_source)


async def __play(media: str):
    """
    @param      media       Youtube Audio Source URL
    """
    global media_player
    global event_manager
    global voice_client

    if voice_client:
        await __play_voice_client(media)

    # It'll interrupt the currently playing music
    media_player.set_mrl(media)
    media_player.play()


async def __play_voice_client(media: str):

    FFMPEG_OPTS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    if not voice_client.is_connected():
        await __setup_voice_client()

    # TODO: We should wait for the music to stop, but for now we'll cut it off.
    if voice_client.is_playing():
        voice_client.stop()

    voice_client.play(
        discord.FFmpegPCMAudio(media, **FFMPEG_OPTS),
        after=lambda e: print("Voice Client finished playing song")
    )
    voice_client.source = discord.PCMVolumeTransformer(voice_client.source, volume=0.5)


def __video_finished(event):
    print(f"Finished {event}")

    bot.loop.create_task(playNext())


# Start bot
try:
    bot.run(os.getenv('TOKEN'), bot=True)
finally:
    # Close the VLC media player
    print("Cleaning up...")

    if media_player:
        media_player.release()
