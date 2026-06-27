from db import init_db, SessionLocal, Games, PlayerMatchStats


# GAME TO ADD
gameweek = 0
home_team = "Piacenza"
away_team = "Verona"
score_loser = 2
won = "Piacenza"

init_db()
db = SessionLocal()

played = [
    Games(week = gameweek, home = home_team, away = away_team, score=score_loser, winner = won)
]

db.add_all(played)
db.commit()

print("Game added")