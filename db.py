# db.py
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Boolean, Float, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ── Models ──────────────────────────────────────────

class Manager(Base):
    __tablename__ = "managers"
    id         = Column(Integer, primary_key=True)
    # discord_id = Column(String, nullable=False)
    discord_id = Column(String, unique=True, nullable=False)
    team_name  = Column(String, unique=True, nullable=False)
    logo_url   = Column(String, nullable=True)   # ← add this
    team     = Column(String, nullable=False)  # credits for auction drafts
    joined_at  = Column(DateTime, default=datetime.utcnow)

    roster = relationship("Roster", back_populates="manager")

class Player(Base):
    __tablename__ = "players"
    id         = Column(Integer, primary_key=True)
    name       = Column(String, nullable=False)
    team       = Column(String)           # SuperLega club (e.g. "Trentino")
    role       = Column(String)           # setter, libero, outside, middle, opposite
    drafted    = Column(String, default = "_")

class Roster(Base):
    __tablename__ = "rosters"
    id         = Column(Integer, primary_key=True)
    manager_id = Column(Integer, ForeignKey("managers.id"))
    player_id  = Column(Integer, ForeignKey("players.id"))
    is_starter = Column(Boolean, default=False)
    is_captain = Column(Boolean, default=False)
    gameweek   = Column(Integer, default=1)

    manager = relationship("Manager", back_populates="roster")
    player  = relationship("Player")

class DraftSession(Base):
    __tablename__ = "draft_sessions"
    id           = Column(Integer, primary_key=True)
    gameweek     = Column(Integer, default=1)
    status       = Column(String, default="pending")  # pending/active/done
    current_pick = Column(Integer, default=0)
    started_at   = Column(DateTime, default=datetime.utcnow)

    picks = relationship("DraftPick", back_populates="session")

class DraftPick(Base):
    __tablename__ = "draft_picks"
    id          = Column(Integer, primary_key=True)
    session_id  = Column(Integer, ForeignKey("draft_sessions.id"))
    manager_id  = Column(Integer, ForeignKey("managers.id"))
    player_id   = Column(Integer, ForeignKey("players.id"))
    pick_number = Column(Integer)

    session = relationship("DraftSession", back_populates="picks")
    manager = relationship("Manager")
    player  = relationship("Player")

class Games(Base):
    __tablename__ = "games"
    id          = Column(Integer, primary_key=True)
    week        = Column(Integer)
    home        = Column(String)
    away        = Column(String)
    score       = Column(Integer)
    winner      = Column(String)

    stats    = relationship("PlayerMatchStats", back_populates="match")  # ← added

# add this class alongside your other models in db.py
class LeagueState(Base):
    __tablename__ = "league_state"
    id    = Column(Integer, primary_key=True)
    key   = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)


class PlayerMatchStats(Base):
    __tablename__ = "player_stats"
    id          = Column(Integer, primary_key=True)
    match_id    = Column(Integer,ForeignKey("games.id"))
    player_id   = Column(Integer, ForeignKey("players.id"))

    # -- Attacking --
    attack_points   = Column(Integer, default=0)
    attack_errors   = Column(Integer, default=0)
    attack_attempts = Column(Integer, default=0)
    attack_eff      = Column(Float,   default=0.0)

    # -- Blocking --
    block_points    = Column(Integer, default=0)

    # -- Serving --
    serve_points   = Column(Integer, default=0)
    serve_errors   = Column(Integer, default=0)
    serve_attempts = Column(Integer, default=0)
    serve_eff      = Column(Float,   default=0.0)

    # -- Reception --
    reception_ok       = Column(Integer, default=0)
    reception_per      = Column(Integer, default=0)
    reception_attempts = Column(Integer, default=0)
    reception_score    = Column(Float,   default=0.0)
    digs               = Column(Integer, default=0)

    # -- Setting --
    set_assists   = Column(Integer, default=0)

    # Points earned in the game
    fantasy_points  = Column(Integer, default=0)

    match  = relationship("Games",  back_populates="stats")
    player = relationship("Player")

class FantasyMatchup(Base):
    __tablename__   = "fantasy_matchups"
    id              = Column(Integer, primary_key=True)
    gameweek        = Column(Integer)
    home_manager_id = Column(Integer, ForeignKey("managers.id"))
    away_manager_id = Column(Integer, ForeignKey("managers.id"))
    home_points     = Column(Integer, default=0)
    away_points     = Column(Integer, default=0)
    winner_id       = Column(Integer, ForeignKey("managers.id"), nullable=True)

# ── Helpers ─────────────────────────────────────────

def init_db():
    Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()

# add these helper functions near init_db()
def get_state(db, key: str, default: str = None) -> str:
    row = db.query(LeagueState).filter_by(key=key).first()
    return row.value if row else default

def set_state(db, key: str, value: str):
    row = db.query(LeagueState).filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.add(LeagueState(key=key, value=value))
    db.commit()

def calculate_fantasy_points(role: str, stats: dict) -> int:
    pts = 0

    if role in ("outside", "opposite", "middle"):
        pts += stats.get("attack_points", 0) * 3
        pts += stats.get("block_points",  0) * 4
        pts += stats.get("serve_points",  0) * 4
        eff = stats.get("attack_eff", 0.0)
        if stats.get("attack_attempts", 0) >= 5:
            if eff > 50:   pts += 3
            elif eff > 30: pts += 1
            elif eff < 0:  pts -= 2

    elif role == "setter":
        pts += stats.get("set_assists",  0) * 1
        pts += stats.get("block_points", 0) * 4
        pts += stats.get("serve_points", 0) * 4

    elif role == "libero":
        pts += stats.get("reception_ok", 0) * 1
        pts += stats.get("digs",         0) * 2
        eff = stats.get("reception_score", 0.0)
        if eff > 60:   pts += 3
        elif eff > 40: pts += 1

    # universal — errors cost points
    pts -= stats.get("attack_errors", 0) * 1
    pts -= stats.get("serve_errors",  0) * 1

    return max(pts, 0)