from db import init_db, SessionLocal, Games, Player, PlayerMatchStats, calculate_fantasy_points

# Helper functions for efficiencies
def eff(kill,err,att):
    return (kill-err)/att*100 if att!=0 else 0

def assists(kill,tot):
    return max(tot-kill,0)

# GAME TO ADD
gameweek = 0
home_team = "Piacenza"
away_team = "Verona"
score_loser = 2
won = "Piacenza"

init_db()
db = SessionLocal()

game = Games(
    week = gameweek,
    home = home_team,
    away = away_team,
    score=score_loser, 
    winner = won
)
db.add(game)
db.commit()
db.refresh(game)

print(f"Game created — ID: {game.id}")

HOME_KILLS = 58
home_stats = [
    ("Gutierrez Jose Miguel", "Piacenza",  17,  7, 35,  0,  2,  0,  0,   0,  0,  0,   4,  0),
    ("Galassi Gianluca",      "Piacenza",   9,  1, 13,  3,  3,  2,  0,   0,  0,  0,   0,  0),
    ("Mandiraci Ramazan Efe", "Piacenza",  12,  3, 34,  1,  1,  0,  0,   5,  0,  0,   2,  0),
    ("Bovolenta Alessandro",  "Piacenza",   8,  4, 20,  1,  0,  0,  0,   3,  0,  0,   3,  0),
    ("Comparoni Francesco",   "Piacenza",   6,  1,  9,  2,  3,  4,  0,   1,  0,  0,   1,  0),
    ("Leon Henri Emmanuel",   "Piacenza",   4,  1, 11,  1,  1,  2,  0,   1,  0,  0,   1,  0),
    ("Porro Paolo",           "Piacenza",   1,  0,  2,  1,  2,  3, 99,   2,  0,  0,   2,  assists(HOME_KILLS, 1)),
    ("Travica Dragan",        "Piacenza",   0,  0,  1,  0,  0,  1, 12,   0,  0,  0,   0,  assists(HOME_KILLS, 0)),
    ("Bergmann Lukas Felipe", "Piacenza",   1,  2,  5,  0,  0,  1,  0,   1,  0,  0,   1,  0),
    ("Pace Domenico",         "Piacenza",   0,  0,  0,  0,  0,  0,  0,   5,  0, 24,   8,  0),
    ("Andringa Robbert",      "Piacenza",   0,  0,  0,  0,  0,  0,  0,   1,  0,  1,   0,  0),
    ("Loreti Luca",           "Piacenza",   0,  0,  0,  0,  0,  0,  0,   0,  0,  0,   2,  0),
    ("Seddik Joris",          "Piacenza",   0,  1,  1,  0,  0,  0,  0,   0,  0,  0,   0,  0),
    ("Fraleone",              "Piacenza",   0,  0,  0,  0,  0,  0,  0,   0,  0,  0,   0,  0),
]


AWAY_KILLS = 64
away_stats = [
    # (name, team, atk, err, att, blk, srv, sre, srv_att, rec_ok, rec_per, rec_att, digs, ast)
    ("Keita Noumory",          "Verona",  29,  5, 44,  1,  1,  1,  2,   0,  0, 15,   3,  0),
    ("Mozic Rok",              "Verona",  11,  5, 22,  1,  0,  3, 10,   5,  0, 20,   2,  0),
    ("Vitelli Marco",          "Verona",   7,  1, 10,  2,  0, 11, 18,   0,  0,  3,   4,  0),
    ("Nedeljkovic Aleksandar", "Verona",   5,  0,  8,  3,  0,  4, 15,   0,  0,  5,   3,  0),
    ("Sani Francesco",         "Verona",   7,  2, 15,  0,  0,  3,  3,   0,  0,  0,   6,  0),
    ("Christenson Micah",      "Verona",   3,  0,  3,  2,  1,  0, 85,   0,  0,  0,   6,  assists(AWAY_KILLS, 3)),
    ("Ferreira Souza Darlan",  "Verona",   2,  0,  3,  1,  1,  0,  1,   0,  0,  1,   0,  0),
    ("Cortesia Lorenzo",       "Verona",   0,  0,  1,  0,  0,  0,  0,   0,  0,  0,   1,  0),
    ("Valbusa Marco",          "Verona",   0,  0,  0,  0,  0,  0,  0,   0,  0,  0,   0,  0),
    ("Gironi Fabrizio",        "Verona",   0,  0,  0,  0,  0,  0,  0,   0,  0,  0,   0,  0),
    ("Planinsic Uros",         "Verona",   0,  0,  0,  0,  0,  0,  0,   0,  0,  0,   1,  assists(AWAY_KILLS, 0)),
    ("Staforini Matteo",       "Verona",   0,  1,  6,  0,  0,  1,  5,   5,  0, 27,   9,  0),
    ("Bonisoli Pietro",        "Verona",   0,  0,  0,  0,  0,  0,  0,   0,  0,  0,   0,  0),
    ("Glatz Lukas",            "Verona",   0,  0,  1,  0,  0,  1,  4,   1,  0,  4,   0,  0),
]
# ── Insert stats ───────────────────────────────────────────────────
def insert_stats(stats_list):
    inserted = 0
    skipped  = 0
    total_pts = 0
    # (player_name, team, atk, err, att, blk, srv, sre, srv_att, rec_ok, rec_per, rec_att, digs, ast)
    for (player_name, team, atk, err, att, blk, srv, sre, srv_att, rec_ok, rec_per, rec_att, digs, ast) in stats_list:

        player = db.query(Player).filter(
            Player.name.ilike(f"%{player_name}%"),
            Player.team == team
        ).first()

        if not player:
            print(f"  ⚠️  Not found: {player_name} ({team}) — skipping")
            skipped += 1
            continue

        a_eff = eff(atk, err, att)
        s_eff = eff(srv, sre, srv_att)
        r_eff = eff(rec_ok, 0, rec_att) if rec_att > 0 else 0.0

        pts = calculate_fantasy_points(player.role, {
            "attack_points":   atk,
            "attack_errors":   err,
            "attack_attempts": att,
            "attack_eff":      a_eff,
            "block_points":    blk,
            "serve_points":    srv,
            "serve_errors":    sre,
            "reception_ok":    rec_ok,
            "reception_score": r_eff,
            "digs":            digs,
            "set_assists":     ast,
        })

        db.add(PlayerMatchStats(
            match_id           = game.id,
            player_id          = player.id,
            attack_points      = atk,
            attack_errors      = err,
            attack_attempts    = att,
            attack_eff         = a_eff,
            block_points       = blk,
            serve_points       = srv,
            serve_errors       = sre,
            serve_attempts     = srv_att,
            serve_eff          = s_eff,
            reception_ok       = rec_ok,
            reception_per      = rec_per,
            reception_attempts = rec_att,
            reception_score    = r_eff,
            digs               = digs,
            set_assists        = ast,
            fantasy_points     = pts
        ))
        total_pts+=pts

        print(f"  ✅ {player_name:<30} ({player.role:<8}) → {pts} pts")
        inserted += 1

    db.commit()
    print(f"  {inserted} inserted, {skipped} skipped\n")
    print(f"A total of {total_pts} was earned from the players on this team")



print(f"\n── {home_team} ──")
insert_stats(home_stats)

print(f"── {away_team} ──")
insert_stats(away_stats)

db.close()
print("Done!")


# Stats to add for the games:
# match_id    = Column(Integer,ForeignKey("games.id"))
# player_id   = Column(Integer, ForeignKey("players.id"))

# # -- Attacking --
# attack_points   = Column(Integer, default=0)
# attack_errors   = Column(Integer, default=0)
# attack_attempts = Column(Integer, default=0)
# attack_eff      = Column(Float,   default=0.0)

# # -- Blocking --
# block_points    = Column(Integer, default=0)

# # -- Serving --
# serve_points   = Column(Integer, default=0)
# serve_errors   = Column(Integer, default=0)
# serve_attempts = Column(Integer, default=0)
# serve_eff      = Column(Float,   default=0.0)

# # -- Reception --
# reception_ok       = Column(Integer, default=0)
# reception_per      = Column(Integer, default=0)
# reception_attempts = Column(Integer, default=0)
# reception_score    = Column(Float,   default=0.0)

# # -- Setting --
# set_assists   = Column(Integer, default=0)

# # Points earned in the game
# fantasy_points  = Column(Integer, default=0)

# match  = relationship("Games",  back_populates="stats")
# player = relationship("Player")
# home = [
#     PlayerMatchStats(match_id = match.id, player_id = player.id, attack_point = 5),
# ]

# away = [

# ]