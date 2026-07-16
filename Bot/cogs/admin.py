# cogs/admin.py
import discord
import subprocess
import sys
from pathlib import Path
from discord import app_commands
from discord.ext import commands
from sqlalchemy import text
from db import SessionLocal, Manager, init_db, Player, FantasyMatchup, WeeklyAward, get_state, set_state, generate_schedule
# from db import SessionLocal, Manager, init_db, WeeklyAward, Player, get_state, generate_schedule
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
    async def team_logo(self, interaction: discord.Interaction, 
                        logo: discord.Attachment):
        db = SessionLocal()
        try:
            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()
            if not manager:
                await interaction.response.send_message(
                    "You're not registered.", ephemeral=True
                )
                return

            # save file locally to assets/logos/
            import aiohttp
            from pathlib import Path

            logo_dir = Path(__file__).parent.parent.parent / "assets" / "logos"
            logo_dir.mkdir(exist_ok=True)

            # filename based on team name
            filename = manager.team_name.lower().replace(" ", "_") + ".png"
            filepath = logo_dir / filename

            # download and save
            async with aiohttp.ClientSession() as session:
                async with session.get(logo.url) as resp:
                    with open(filepath, "wb") as f:
                        f.write(await resp.read())

            # store the local web path in the database
            manager.logo_url = f"/assets/logos/{filename}"
            db.commit()

            await interaction.response.send_message(
                f"✅ Logo saved for **{manager.team_name}**.", ephemeral=True
            )
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

    @app_commands.command(name="awards", description="Who got the awards this week")
    async def awards(self, interaction: discord.Interaction):
        await interaction.response.defer()   # defer immediately — prevents timeout and double-response issues
        db = SessionLocal()
        try:
            gw = int(get_state(db, "current_gameweek", "0"))
            # gw = 0

            # auto-calculate if not done yet
            existing = db.query(WeeklyAward).filter_by(gameweek=gw).first()
            if not existing:
                try:
                    calculate_weekly_awards(db, gw)
                except Exception as e:
                    await interaction.followup.send(
                        f"❌ Failed to calculate awards: `{e}`", ephemeral=True
                    )
                    return

            award_rows = db.query(WeeklyAward).filter_by(gameweek=gw).all()

            if not award_rows:
                await interaction.followup.send(
                    f"No stats found for Gameweek {gw} yet — make sure games have been added.",
                    ephemeral=True
                )
                return

            icons = {
                "motw":         "👑 Manager of the Week",
                "spike_king":   "⚡ Spike King",
                "the_wall":     "🧱 The Wall",
                "digs_machine": "🛡️ Digs Machine",
                "ace_master":   "🎯 Ace Master",
            }

            lines = [f"🏆 **Gameweek {gw} Awards**\n"]
            for a in award_rows:
                mgr = db.get(Manager, a.manager_id)
                icon = icons.get(a.award_type, "🏅")
                if a.player_id:
                    player = db.get(Player, a.player_id)
                    lines.append(
                        f"{icon}: **{player.name}** ({mgr.team_name}) — {a.stat_value}"
                    )
                else:
                    lines.append(f"{icon}: **{mgr.team_name}** — {a.stat_value} pts")

            await interaction.followup.send("\n".join(lines))

        finally:
            db.close()
    
    @app_commands.command(name="season_start",
                      description="Generate the full season schedule (admin only)")
    @app_commands.describe(double_rr="Play home and away? (default: single round robin)")
    async def season_start(self, interaction: discord.Interaction,
                        double_rr: bool = False):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        db = SessionLocal()
        try:
            managers = db.query(Manager).all()
            if len(managers) < 2:
                await interaction.response.send_message(
                    "Need at least 2 managers registered.", ephemeral=True
                )
                return

            ids = [m.id for m in managers]
            schedule = generate_schedule(ids)

            # if double round robin, add a return leg with home/away swapped
            if double_rr:
                n_gws = len(schedule)
                return_leg = {}
                for gw, pairs in schedule.items():
                    return_leg[gw + n_gws] = [(away, home) for home, away in pairs]
                schedule.update(return_leg)

            # clear any existing matchups and insert the new schedule
            db.query(FantasyMatchup).delete()
            for gw, pairs in schedule.items():
                for home_id, away_id in pairs:
                    db.add(FantasyMatchup(
                        gameweek=gw,
                        home_manager_id=home_id,
                        away_manager_id=away_id,
                    ))

            total_gws = len(schedule)
            set_state(db, "total_gameweeks", str(total_gws))
            set_state(db, "current_gameweek", "1")
            db.commit()

            # build announcement
            mgr_map = {m.id: m.team_name for m in managers}
            lines = [f"📅 **Season schedule generated — {total_gws} gameweeks**\n"]
            for gw in sorted(schedule.keys()):
                lines.append(f"**GW{gw}:**")
                for home, away in schedule[gw]:
                    lines.append(f"  {mgr_map[home]} vs {mgr_map[away]}")

            await interaction.response.send_message("\n".join(lines))

        finally:
            db.close()

    @app_commands.command(name="gameweek_finalise",
                      description="Finalise the current gameweek (admin only)")
    async def gameweek_finalise(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Admin only.", ephemeral=True)
            return

        await interaction.response.defer()
        db = SessionLocal()
        try:
            gw = int(get_state(db, "current_gameweek", "1"))

            # get game IDs for this week
            game_ids = [r.id for r in db.execute(
                text("SELECT id FROM games WHERE week=:gw"), {"gw": gw}
            ).fetchall()]

            if not game_ids:
                await interaction.followup.send(
                    f"No games found for GW{gw}. Add games first.", ephemeral=True
                )
                return

            placeholders = ",".join(str(g) for g in game_ids)

            # calculate each manager's fantasy score for this GW
            scores = db.execute(text(f"""
                SELECT r.manager_id, COALESCE(SUM(ps.fantasy_points), 0) AS total
                FROM rosters r
                JOIN player_stats ps ON ps.player_id = r.player_id
                    AND ps.match_id IN ({placeholders})
                WHERE r.gameweek = :gw AND r.is_starter = 1
                GROUP BY r.manager_id
            """), {"gw": gw}).fetchall()

            score_map = {r.manager_id: r.total for r in scores}

            # update matchup results
            matchups = db.query(FantasyMatchup).filter_by(gameweek=gw).all()
            results = []
            for m in matchups:
                hp = score_map.get(m.home_manager_id, 0)
                ap = score_map.get(m.away_manager_id, 0)
                m.home_points = hp
                m.away_points = ap
                m.winner_id = (m.home_manager_id if hp > ap
                            else m.away_manager_id if ap > hp
                            else None)
                home_mgr = db.get(Manager, m.home_manager_id)
                away_mgr = db.get(Manager, m.away_manager_id)
                results.append((home_mgr.team_name, hp, ap,
                                away_mgr.team_name, m.winner_id,
                                home_mgr, away_mgr))

            # calculate weekly awards
            calculate_weekly_awards(db, gw)
            db.commit()

            # post results
            lines = [f"🏁 **Gameweek {gw} Results**\n"]
            for home_name, hp, ap, away_name, winner_id, hm, am in results:
                winner = hm.team_name if winner_id == hm.id else (
                        am.team_name if winner_id == am.id else "Draw")
                lines.append(f"**{home_name}** {hp} — {ap} **{away_name}** → {winner}")

            await interaction.followup.send("\n".join(lines))

        finally:
            db.close()
    
def calculate_weekly_awards(db, gameweek: int):
    from sqlalchemy import text

    AWARD_MOTW         = "motw"
    AWARD_SPIKE_KING   = "spike_king"
    AWARD_THE_WALL     = "the_wall"
    AWARD_DIGS_MACHINE = "digs_machine"
    AWARD_ACE_MASTER   = "ace_master"

    # get game IDs for this gameweek
    game_ids = db.execute(text(
        "SELECT id FROM games WHERE week = :gw"
    ), {"gw": gameweek}).fetchall()
    gids = [r.id for r in game_ids]

    print(f"[awards] GW{gameweek} — found {len(gids)} games: {gids}")

    if not gids:
        print("[awards] No games found, aborting.")
        return

    placeholders = ",".join(str(g) for g in gids)

    # ── player-level awards ───────────────────────────────────────
    # NOTE: removed the is_starter filter — award goes to whoever
    # had the best stats regardless of roster status
    stat_awards = [
        (AWARD_SPIKE_KING,   "attack_points"),
        (AWARD_THE_WALL,     "block_points"),
        (AWARD_DIGS_MACHINE, "digs"),
        (AWARD_ACE_MASTER,   "serve_points"),
    ]

    for award_type, stat_col in stat_awards:
        row = db.execute(text(f"""
            SELECT ps.player_id, SUM(ps.{stat_col}) AS total,
                   r.manager_id
            FROM player_stats ps
            LEFT JOIN rosters r ON r.player_id = ps.player_id
                AND r.gameweek = :gw
            WHERE ps.match_id IN ({placeholders})
            GROUP BY ps.player_id
            ORDER BY total DESC
            LIMIT 1
        """), {"gw": gameweek}).fetchone()

        print(f"[awards] {award_type}: player_id={row.player_id if row else None}, "
              f"total={row.total if row else 0}, manager={row.manager_id if row else None}")

        if row and row.total and row.total > 0 and row.manager_id:
            db.add(WeeklyAward(
                gameweek   = gameweek,
                award_type = award_type,
                manager_id = row.manager_id,
                player_id  = row.player_id,
                stat_value = int(row.total)
            ))
            print(f"[awards] ✅ Added {award_type}")
        else:
            print(f"[awards] ⚠️ Skipped {award_type} — no valid row or manager_id is None")

    # ── manager of the week ────────────────────────────────────────
    motw = db.execute(text(f"""
        SELECT r.manager_id, SUM(ps.fantasy_points) AS total
        FROM player_stats ps
        JOIN rosters r ON r.player_id = ps.player_id
            AND r.gameweek = :gw
        WHERE ps.match_id IN ({placeholders})
        GROUP BY r.manager_id
        ORDER BY total DESC
        LIMIT 1
    """), {"gw": gameweek}).fetchone()

    print(f"[awards] motw: manager_id={motw.manager_id if motw else None}, "
          f"total={motw.total if motw else 0}")

    if motw and motw.total and motw.total > 0:
        db.add(WeeklyAward(
            gameweek   = gameweek,
            award_type = AWARD_MOTW,
            manager_id = motw.manager_id,
            player_id  = None,
            stat_value = int(motw.total)
        ))
        print("[awards] ✅ Added motw")

    db.commit()
    print("[awards] ✅ Committed all awards")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))