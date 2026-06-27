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
    budget     = Column(Integer, default=100)  # credits for auction drafts
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

    # -- Setting --
    set_assists   = Column(Integer, default=0)

    # Points earned in the game
    fantasy_points  = Column(Integer, default=0)

    match  = relationship("Games",  back_populates="stats")
    player = relationship("Player")



# ── Helpers ─────────────────────────────────────────

def init_db():
    Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()