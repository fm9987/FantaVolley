# utils.py
import discord
from functools import wraps

def channel_only(channel_id_getter):
    """
    Restrict a command to a specific channel.
    Usage:
        @channel_only(lambda: config.CHANNEL_ADMIN)
        async def my_command(self, interaction): ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            allowed_id = channel_id_getter()
            if interaction.channel_id != allowed_id:
                channel = interaction.guild.get_channel(allowed_id)
                mention = channel.mention if channel else "the correct channel"
                await interaction.response.send_message(
                    f"This command only works in {mention}.",
                    ephemeral=True
                )
                return
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator