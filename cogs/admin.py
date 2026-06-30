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
    @app_commands.describe(team_name="Your team's name")
    async def register(self, interaction: discord.Interaction, team_name: str):
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

            manager = Manager(discord_id=discord_id, team_name=team_name)
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

    # ── /myteam ───────────────────────────────────────────────────────────────

    @app_commands.command(name="myteam", description="View your current roster")
    async def myteam(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()

            if not manager:
                await interaction.response.send_message(
                    "You haven't registered yet. Use /register first.", ephemeral=True
                )
                return

            starters = [r for r in manager.roster if r.is_starter]
            bench    = [r for r in manager.roster if not r.is_starter]

            embed = discord.Embed(title=manager.team_name, color=discord.Color.blue())

            if manager.logo_url:
                embed.set_thumbnail(url=manager.logo_url)

            starter_lines = (
                "\n".join(f"• {r.player.name} ({r.player.role})" for r in starters)
                or "— empty —"
            )
            bench_lines = (
                "\n".join(f"• {r.player.name} ({r.player.role})" for r in bench)
                or "— empty —"
            )

            embed.add_field(name="Starters", value=starter_lines, inline=False)
            embed.add_field(name="Bench",    value=bench_lines,   inline=False)
            embed.set_footer(text=f"Budget: {manager.budget} credits")

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

    # ── /seed_players ─────────────────────────────────────────────────────────

    @app_commands.command(name="seed_players", description="Run the seed_players script (admin only)")
    @channel_only(lambda: config.CHANNEL_ADMIN)
    async def seed_players(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            script = Path(__file__).parent.parent / "seed_players.py"
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout or result.stderr or "No output"
            status = "✅" if result.returncode == 0 else "❌"
            await interaction.followup.send(
                f"{status} seed_players.py ran:\n```\n{output[:1900]}\n```",
                ephemeral=True
            )
        except subprocess.TimeoutExpired:
            await interaction.followup.send("❌ Script timed out.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    # ── /add_game ─────────────────────────────────────────────────────────────

    @app_commands.command(name="add_game", description="Run the add_game script (admin only)")
    @channel_only(lambda: config.CHANNEL_ADMIN)
    async def add_game(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            script = Path(__file__).parent.parent / "add_game.py"
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout or result.stderr or "No output"
            status = "✅" if result.returncode == 0 else "❌"
            await interaction.followup.send(
                f"{status} add_game.py ran:\n```\n{output[:1900]}\n```",
                ephemeral=True
            )
        except subprocess.TimeoutExpired:
            await interaction.followup.send("❌ Script timed out.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

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

            lineup_ch = self.bot.get_channel(config.CHANNEL_LINEUP)
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

            lineup_ch = self.bot.get_channel(config.CHANNEL_LINEUP)
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