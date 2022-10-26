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

intents = discord.Intents.default()

# Bot Instance
bot: commands.Bot = commands.Bot(
    command_prefix=os.getenv('COMMAND_PREFIX', default='$'),
    intents=intents
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

    global bot
    global text_channel
    global voice_channel
    global playlist
    global music_queue

    await bot.tree.sync()

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

    await __play_next()


@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author != bot.user:
        # Ignore messages written by other users
        return

    if reaction.me:
        # Ignore Reactions made by bot
        return

    # TODO:
    # 1. add-cmd lists multiple videos -> select correct video through reaction?
    # 2. after adding video -> react to revert action?


#
# Bot Commands
#
@bot.tree.command()
async def connect(interaction: discord.Interaction):
    """
    Manually connect bot to voice channel if e.g. disconnected
    """
    await __setup_voice_client()
    await interaction.response.send_message(content="Connected!", ephemeral=True)


@bot.tree.command(description='Adds a song to the playlist')
async def add(interaction: discord.Interaction, url: str):
    """
    Add video to playlist
    @param      ctx     Discord Text-Channel in which command was used
    @param      query     Youtube-Link or Title (YT searches automatically and returns first video found)
    """

    await interaction.response.send_message(content=f"Searching video: <{url}>", ephemeral=True)

    try:
        video_data = yt_utils.get_video_data_with_ytdl(url)
    except yt_utils.YTLookupError:
        await interaction.followup.send_message(content="Failed to retrieve Video data", ephemeral=True)
        return
    except yt_utils.DurationPolicyError:
        await interaction.followup.send_message(
            content="Video-Duration-Policy violated: Video duration is too long (Max. 12min)",
            ephemeral=True
        )
        return

    global playlist
    if playlist.item_exists(video_data):
        await interaction.followup.send_message(content="Video is already in playlist", ephemeral=True)
        return

    playlist.add_item(video_data)
    playlist.save()

    music_queue.enqueue_item(video_data)

    # Send Embed
    embed = discord.Embed(
        title=f"Added {video_data.title} to playlist",
        description=f"{video_data.url}"
    )
    embed.set_thumbnail(url=video_data.thumbnail)
    await interaction.followup.send_message(content=None, embed=embed)


#
# TODO: Cleanup and refactor mark, unmark and meme command
#
@bot.tree.command()
async def mark(interaction: discord.Interaction, key: str, video: str):
    try:
        with open('marked.json', 'r') as file:
            marked = json.load(file)
    except:
        print("marked.json could not be loaded")
        marked = {}

    if key in marked:
        await interaction.response.send_message("Key already exists. Unmark first or use another.", ephemeral=True)
        return

    marked[key] = yt_utils.get_video_data_with_ytdl(video)

    with open('marked.json', 'w') as file:
        json.dump(marked, file, indent=4)

    await interaction.response.send_message("Key applied", ephemeral=True)


@bot.tree.command()
async def unmark(interaction: discord.Interaction, key: str):
    await interaction.response.send_message(f"The key '{key}' has been freed", ephemeral=True)


@bot.tree.command()
async def meme(interaction: discord.Interaction, key: str):
    try:
        with open('marked.json', 'r') as file:
            marked = json.load(file)
    except:
        print("marked.json could not be loaded")
        return

    if key in marked:
        media_player.stop()
        voice_client.stop()
        await __play_next(marked[key])
        await interaction.response.send_message("Ehehehe", ephemeral=True)
    else:
        await interaction.response.send_message("Key not found", ephemeral=True)


@bot.tree.command()
async def play(interaction: discord.Interaction):
    """
    Manual play command
    """
    await __play_next()
    await interaction.response.send_message(content=f'Now playing.', ephemeral=True)


@bot.tree.command()
async def stop(interaction: discord.Interaction):
    """
    Manual stop command
    """
    global media_player
    global voice_client
    media_player.stop()
    voice_client.stop()
    await interaction.response.send_message(content=f'Stopped playing.', ephemeral=True)


@bot.tree.command()
async def volume(interaction: discord.Interaction, level: int):
    level = max(100, min(0, level))
    media_player.audio_set_volume(level)
    await interaction.response.send_message(content=f'Volume set to{level}.', ephemeral=True)


async def __setup_voice_client():
    """
    Connect Bot to music voice channel
    """
    global voice_client
    global voice_channel

    if voice_channel is None:
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=voice_channel.guild)

    # First check if there's a voice client already connected to a channel in the server.
    # If not, create a new voice client.
    if voice_client is None or not voice_client.is_connected():
        voice_client = await voice_channel.connect()

    # Already connected and in the right channel
    if voice_client.channel == voice_channel:
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

    media_player = vlc.MediaPlayer()
    event_manager = media_player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, __video_finished)


async def __play_next(video: Video = None):
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

    bot.loop.create_task(__play_next())


# Start bot
try:
    bot.run(os.getenv('TOKEN'))
finally:
    # Close the VLC media player
    print("Cleaning up...")

    if media_player:
        media_player.release()
