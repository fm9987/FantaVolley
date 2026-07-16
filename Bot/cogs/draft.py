# cogs/draft.py
import discord
import random
from discord import app_commands
from discord.ext import commands
from db import SessionLocal, Manager, Player, DraftSession, DraftPick, Roster

ROSTER_SIZE = 12   # total players per team
STARTERS    = 6    # how many are marked as starters

class Draft(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # draft order stored in memory during an active draft
        # list of manager IDs in current pick order
        self.draft_order: list[int] = []

    # ── helper: who picks next ───────────────────────────────────────────────

    def _current_manager_id(self, session: DraftSession) -> int | None:
        """Return the manager_id whose turn it is, or None if draft is over."""
        picks_made = session.current_pick
        total      = len(self.draft_order) * ROSTER_SIZE
        if picks_made >= total:
            return None
        # snake: even rounds go forward, odd rounds go backward
        round_num  = picks_made // len(self.draft_order)
        pos        = picks_made  % len(self.draft_order)
        if round_num % 2 == 1:
            pos = len(self.draft_order) - 1 - pos
        return self.draft_order[pos]

    # ── /draft start ─────────────────────────────────────────────────────────

    @app_commands.command(name="draft_start", description="Start a new snake draft (admin only)")
    async def draft_start(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            # check there are managers to draft
            managers = db.query(Manager).all()
            if len(managers) < 2:
                await interaction.response.send_message(
                    "Need at least 2 registered managers to start a draft. "
                    "Use `/register` first.", ephemeral=True
                )
                return

            # check no draft already active
            active = db.query(DraftSession).filter_by(status="active").first()
            if active:
                await interaction.response.send_message(
                    "A draft is already in progress!", ephemeral=True
                )
                return

            # check enough players exist
            player_count = db.query(Player).count()
            needed       = len(managers) * ROSTER_SIZE
            if player_count < needed:
                await interaction.response.send_message(
                    f"Not enough players in the database. "
                    f"Need {needed}, have {player_count}.", ephemeral=True
                )
                return

            # create draft session
            session = DraftSession(status="active", current_pick=0)
            db.add(session)
            db.commit()
            db.refresh(session)

            # randomize draft order and store in memory
            self.draft_order = [m.id for m in managers]
            random.shuffle(self.draft_order)

            # build order display
            order_names = []
            for mid in self.draft_order:
                m = db.query(Manager).get(mid)
                order_names.append(f"**{m.team_name}**")

            first_id   = self.draft_order[0]
            first_mgr  = db.query(Manager).get(first_id)

            msg = (
                f"🏐 **Draft has started!**\n\n"
                f"**Pick order (Round 1):** {' → '.join(order_names)}\n"
                f"_(Order reverses each round — snake draft)_\n\n"
                f"<@{first_mgr.discord_id}> you're up first!\n"
                f"Use `/draft_pick [player name]` to make your pick.\n"
                f"Use `/draft_available` to see available players."
            )
            await interaction.response.send_message(msg)

        finally:
            db.close()

    # ── /draft_pick ───────────────────────────────────────────────────────────

    @app_commands.command(name="draft_pick", description="Pick a player during the draft")
    @app_commands.describe(player_name="Name of the player you want to pick")
    async def draft_pick(self, interaction: discord.Interaction, player_name: str):
        db = SessionLocal()
        try:
            # get active draft
            session = db.query(DraftSession).filter_by(status="active").first()
            if not session:
                await interaction.response.send_message(
                    "No draft is currently active.", ephemeral=True
                )
                return

            # check draft order is loaded (bot restart would clear it)
            if not self.draft_order:
                await interaction.response.send_message(
                    "Draft order lost (bot may have restarted). "
                    "Ask an admin to run `/draft_start` again.", ephemeral=True
                )
                return

            # get the calling manager
            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()
            if not manager:
                await interaction.response.send_message(
                    "You're not registered. Use `/register` first.", ephemeral=True
                )
                return

            # is it their turn?
            current_id = self._current_manager_id(session)
            if manager.id != current_id:
                current_mgr = db.query(Manager).get(current_id)
                await interaction.response.send_message(
                    f"It's not your turn! Waiting on **{current_mgr.team_name}**.",
                    ephemeral=True
                )
                return

            # find the player (case-insensitive partial match)
            player = db.query(Player).filter(
                Player.name.ilike(f"%{player_name}%")
            ).first()
            if not player:
                await interaction.response.send_message(
                    f"No player found matching `{player_name}`. "
                    f"Use `/draft_available` to see the list.", ephemeral=True
                )
                return

            # already picked?
            already = db.query(DraftPick).filter_by(
                session_id=session.id, player_id=player.id
            ).first()
            if already:
                await interaction.response.send_message(
                    f"**{player.name}** has already been picked!", ephemeral=True
                )
                return

            # make the pick
            pick_num = session.current_pick + 1
            pick = DraftPick(
                session_id  = session.id,
                manager_id  = manager.id,
                player_id   = player.id,
                pick_number = pick_num
            )
            db.add(pick)

            # add to roster (first STARTERS picks = starter, rest = bench)
            manager_picks = db.query(DraftPick).filter_by(
                session_id=session.id, manager_id=manager.id
            ).count()
            roster_entry = Roster(
                manager_id = manager.id,
                player_id  = player.id,
                is_starter = False
            )
            db.add(roster_entry)

            session.current_pick += 1
            db.commit()

            # check if draft is over
            total_picks = len(self.draft_order) * ROSTER_SIZE
            if session.current_pick >= total_picks:
                session.status = "done"
                db.commit()
                await interaction.response.send_message(
                    f"✅ **{manager.team_name}** picks **{player.name}** "
                    f"({player.role}, {player.team}) — Pick #{pick_num}\n\n"
                    f"🏆 **Draft complete! All teams are full.**"
                )
                return

            # announce pick and next manager
            next_id  = self._current_manager_id(session)
            next_mgr = db.query(Manager).get(next_id)

            # figure out round info
            round_num  = session.current_pick // len(self.draft_order) + 1
            pick_in_rd = session.current_pick  % len(self.draft_order) + 1

            await interaction.response.send_message(
                f"✅ **{manager.team_name}** picks **{player.name}** "
                f"({player.role}, {player.team}) — Pick #{pick_num}\n"
                f"📋 Round {round_num}, pick {pick_in_rd} of {len(self.draft_order)}\n\n"
                f"<@{next_mgr.discord_id}> you're up! Use `/draft_pick [name]`"
            )

        finally:
            db.close()

    # ── /draft_available ──────────────────────────────────────────────────────

    @app_commands.command(name="draft_available", description="List available players in the draft")
    @app_commands.describe(role="Filter by role (optional)")
    @app_commands.choices(role=[
        app_commands.Choice(name="Outside",  value="outside"),
        app_commands.Choice(name="Opposite", value="opposite"),
        app_commands.Choice(name="Setter",   value="setter"),
        app_commands.Choice(name="Middle",   value="middle"),
        app_commands.Choice(name="Libero",   value="libero"),
    ])
    async def draft_available(
        self, interaction: discord.Interaction,
        role: app_commands.Choice[str] = None
    ):
        db = SessionLocal()
        try:
            session = db.query(DraftSession).filter_by(status="active").first()
            if not session:
                await interaction.response.send_message(
                    "No draft is currently active.", ephemeral=True
                )
                return

            # get already picked player IDs
            picked_ids = {
                p.player_id for p in
                db.query(DraftPick).filter_by(session_id=session.id).all()
            }

            # query available
            query = db.query(Player).filter(Player.id.notin_(picked_ids))
            if role:
                query = query.filter_by(role=role.value)
            available = query.order_by(Player.id).all()

            if not available:
                await interaction.response.send_message(
                    "No available players.", ephemeral=True
                )
                return

            role_label = f" ({role.name})" if role else ""
            lines = [f"**Available players{role_label}:**\n"]
            for p in available[:20]:   # cap at 20 to avoid huge messages
                lines.append(
                    f"• **{p.name}** — {p.team} | {p.role} | ⭐ pts"
                )
            if len(available) > 20:
                lines.append(f"_...and {len(available) - 20} more. Filter by role to narrow down._")

            await interaction.response.send_message(
                "\n".join(lines), ephemeral=True
            )
        finally:
            db.close()

    # ── /draft_status ─────────────────────────────────────────────────────────

    @app_commands.command(name="draft_status", description="Show current draft status")
    async def draft_status(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            session = db.query(DraftSession).filter_by(status="active").first()
            if not session:
                await interaction.response.send_message(
                    "No draft is currently active."
                )
                return

            if not self.draft_order:
                await interaction.response.send_message(
                    "Draft order not loaded.", ephemeral=True
                )
                return

            current_id  = self._current_manager_id(session)
            current_mgr = db.query(Manager).get(current_id)
            round_num   = session.current_pick // len(self.draft_order) + 1
            pick_in_rd  = session.current_pick  % len(self.draft_order) + 1
            total_picks = len(self.draft_order) * ROSTER_SIZE

            await interaction.response.send_message(
                f"**Draft status**\n"
                f"Round {round_num} — Pick {pick_in_rd}/{len(self.draft_order)}\n"
                f"Overall: {session.current_pick}/{total_picks} picks made\n\n"
                f"⏳ Waiting on: **{current_mgr.team_name}** (<@{current_mgr.discord_id}>)"
            )
        finally:
            db.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(Draft(bot))