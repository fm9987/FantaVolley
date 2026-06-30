# cogs/admin.py
import discord
import subprocess
import sys
from pathlib import Path
from discord import app_commands
from discord.ext import commands
from db import SessionLocal, Manager, init_db
import config
from utils import channel_only

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db()

    # ── /register ─────────────────────────────────────────────────────────────

    @app_commands.command(name="register", description="Register yourself as a fantasy manager")
    @app_commands.describe(
        team_name="Your team's name",
        associate="The actual SUPERLEGA team to be connected with"
        )
    async def register(self, interaction: discord.Interaction, team_name: str, associate: str):
        db = SessionLocal()
        try:
            discord_id = str(interaction.user.id)

            existing = db.query(Manager).filter_by(discord_id=discord_id).first()
            if existing:
                await interaction.response.send_message(
                    f"You're already registered as **{existing.team_name}**!", ephemeral=True
                )
                return

            name_taken = db.query(Manager).filter_by(team_name=team_name).first()
            if name_taken:
                await interaction.response.send_message(
                    f"The team name **{team_name}** is already taken. Pick another!", ephemeral=True
                )
                return

            manager = Manager(discord_id=discord_id, team_name=team_name, team = associate)
            db.add(manager)
            db.commit()

            await interaction.response.send_message(
                f"✅ **{interaction.user.display_name}** registered as manager of **{team_name}**!"
            )
        finally:
            db.close()

    # ── /team_logo ────────────────────────────────────────────────────────────

    @app_commands.command(name="team_logo", description="Upload your team logo")
    @app_commands.describe(logo="Your team logo image (png, jpg, gif)")
    async def team_logo(self, interaction: discord.Interaction, logo: discord.Attachment):
        db = SessionLocal()
        try:
            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()

            if not manager:
                await interaction.response.send_message(
                    "You're not registered yet. Use /register first.", ephemeral=True
                )
                return

            valid_types = ("image/png", "image/jpeg", "image/gif", "image/webp")
            if logo.content_type not in valid_types:
                await interaction.response.send_message(
                    "Please upload a valid image (PNG, JPG, GIF, or WEBP).", ephemeral=True
                )
                return

            manager.logo_url = logo.url
            db.commit()

            embed = discord.Embed(
                title=f"✅ Logo updated for {manager.team_name}",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=logo.url)
            await interaction.response.send_message(embed=embed)

        finally:
            db.close()


    # ── /managers ─────────────────────────────────────────────────────────────

    @app_commands.command(name="managers", description="List all registered managers")
    async def managers(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            all_managers = db.query(Manager).all()
            if not all_managers:
                await interaction.response.send_message("No managers registered yet.")
                return

            lines = ["**Registered managers:**"]
            for m in all_managers:
                lines.append(f"  • **{m.team_name}** — <@{m.discord_id}>")

            await interaction.response.send_message("\n".join(lines))
        finally:
            db.close()

    # ── /transfers_lock ───────────────────────────────────────────────────────
    @app_commands.command(name="transfers_lock", description="Lock roster changes (admin only)")
    @channel_only(lambda: config.CHANNEL_ADMIN)
    async def transfers_lock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        db = SessionLocal()
        try:
            from db import set_state
            set_state(db, "transfers_locked", "true")

            lineup_ch = self.bot.get_channel(config.CHANNEL_ID)
            if lineup_ch:
                await lineup_ch.send(
                    "🔒 **Transfers and lineup changes are now LOCKED.**\n"
                    "Gameweek has started — no more changes until the admin unlocks."
                )
            await interaction.response.send_message("🔒 Transfers locked.", ephemeral=True)
        finally:
            db.close()

    # ── /transfers_unlock ─────────────────────────────────────────────────────

    @app_commands.command(name="transfers_unlock", description="Unlock roster changes (admin only)")
    @channel_only(lambda: config.CHANNEL_ADMIN)
    async def transfers_unlock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        db = SessionLocal()
        try:
            from db import set_state
            set_state(db, "transfers_locked", "false")

            lineup_ch = self.bot.get_channel(config.CHANNEL_ID)
            if lineup_ch:
                await lineup_ch.send(
                    "🔓 **Transfers and lineup changes are now OPEN.**\n"
                    "Make your changes before the next gameweek starts!"
                )
            await interaction.response.send_message("🔓 Transfers unlocked.", ephemeral=True)
        finally:
            db.close()

    # ── /league_status ────────────────────────────────────────────────────────

    @app_commands.command(name="league_status", description="Check lock status and current gameweek")
    async def league_status(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            from db import get_state
            locked = get_state(db, "transfers_locked", "false") == "true"
            gw     = get_state(db, "current_gameweek", "1")
            status = "🔒 Locked" if locked else "🔓 Open"
            await interaction.response.send_message(
                f"**League status**\n"
                f"Gameweek: **{gw}**\n"
                f"Transfers: **{status}**"
            )
        finally:
            db.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))