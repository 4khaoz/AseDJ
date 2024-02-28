#!/usr/bin/env python3

from typing import Final, Optional

import asyncio
import os

import discord
from dotenv import load_dotenv
import vlc

from talala.playlist import Video
from talala.server import Server, AddTrackError

load_dotenv()

DISCORD_TOKEN: Final[str] = os.getenv("TOKEN")
DISCORD_CHANNEL: Final[ſtr] = os.getenv("CHANNEL")

# Currently we're only interested in guild attributes, events and messages:
# https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents.guild_messages
# https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents.guilds
intents = discord.Intents(guild_messages=True, guilds=True)

# Discord
discord_client = discord.Client(intents=intents)
command_tree = discord.app_commands.CommandTree(discord_client)

# Variables
server: Server = Server()
media_player: Optional[vlc.MediaPlayer] = None
text_channel: Optional[discord.abc.GuildChannel] = None


class AddTrackView(discord.ui.View):

    def __init__(self, track: Video, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.track = track

    @discord.ui.button(
        label="Accept",
        custom_id="accept_track",
        style=discord.enums.ButtonStyle.success,
    )
    async def track_accepted(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.__disable()

        await interaction.response.defer()
        try:
            track = await server.add_track(self.track)
            print(track.youtube_id)
        except AddTrackError as error:
            await interaction.followup.send(content=error, ephemeral=True)
            return

        # Send Embed
        embed = discord.Embed(
            title=f"Added {track.title} to playlist", description=f"{track.url}"
        )
        embed.set_thumbnail(url=track.thumbnail_url)
        await interaction.followup.send(content=None, embed=embed)

    @discord.ui.button(
        label="Reject", custom_id="reject_track", style=discord.enums.ButtonStyle.danger
    )
    async def track_rejected(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.__disable()
        await interaction.response.send_message(
            content="Track rejected", ephemeral=True
        )

    def __disable(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        self.stop()


#
# Discord events
#
@discord_client.event
async def on_ready():
    print("Logged in")

    global text_channel
    global media_player

    await command_tree.sync()

    # Get text channel for event logging
    event_channel_id = DISCORD_CHANNEL
    if event_channel_id:
        text_channel = discord_client.get_channel(int(event_channel_id))
    else:
        print("Will not output events on Discord. No text channel ID specified.")

    media_player = __setup_media_player()

    await server.start()

    await __media_player_next()


#
# Discord commands
#
@command_tree.command(description="Adds a song to the playlist")
async def add(interaction: discord.Interaction, url: str):
    """Add video to playlist"""
    await interaction.response.defer()
    try:
        track = await server.lookup_track(url)
    except AddTrackError as error:
        await interaction.followup.send(content=error, ephemeral=True)
        return

    embed = discord.Embed(
        title=f"Track found: {track.title}.\n\nAccept/reject?",
        description=f"{track.url}",
    )
    embed.set_thumbnail(url=track.thumbnail_url)

    view: AddTrackView = AddTrackView(track=track)

    interaction.extras["track"] = track

    await interaction.followup.send(
        content=None, embed=embed, view=view, ephemeral=True
    )


@command_tree.command()
async def search(interaction: discord.Interaction, term: str):
    """Search tracks that match the search term"""
    tracks = server.search_track(term)
    if len(tracks) == 0:
        await interaction.response.send_message(
            content=f"No tracks found for search term {term}", ephemeral=True
        )
        return
    content = "The following tracks match the search term:\n\n"
    content += "\n".join([f"* [{track.title}](<{track.url}>)" for track in tracks])

    await interaction.response.send_message(content=content)


@command_tree.command()
async def skip(interaction: discord.Interaction):
    """Skip current track"""
    await __media_player_next()
    await interaction.response.send_message(content="Skipped.", ephemeral=True)


@command_tree.command()
async def stop(interaction: discord.Interaction):
    """Stop current track"""
    await __media_player_stop()
    await interaction.response.send_message(content="Stopped.", ephemeral=True)


@command_tree.command()
async def volume(interaction: discord.Interaction, level: int):
    """Change playback volume"""
    level = min(100, max(0, level))
    media_player.audio_set_volume(level)
    await interaction.response.send_message(
        content=f"Volume set to {level}%.", ephemeral=True
    )


def __setup_media_player():
    """Setup a new VLC media player instance and event manager"""
    __media_player = vlc.MediaPlayer()
    event_manager = __media_player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, __video_finished)

    return __media_player


async def __media_player_stop():
    """Stops the current track"""
    if media_player.is_playing():
        media_player.stop()


async def __media_player_next():
    """Plays the next track"""

    current_video, current_source = server.next_track()

    await __media_player_stop()

    # It'll interrupt the currently playing music
    media_player.set_mrl(current_source)
    media_player.play()

    current_video.mark_as_played()

    # Send Embed
    if text_channel:
        embed = discord.Embed(
            title=f"Now playing {current_video.title}",
            description=f"{current_video.url}",
        )
        embed.set_thumbnail(url=current_video.thumbnail_url)
        await text_channel.send(embed=embed)


def __video_finished(event):
    print(f"Finished {event}")

    discord_client.loop.create_task(__media_player_next())


if __name__ == "__main__":
    asyncio.run(discord_client.run(DISCORD_TOKEN))
