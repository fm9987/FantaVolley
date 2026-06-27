# seed_players.py
from db import init_db, SessionLocal, Player

init_db()
db = SessionLocal()

players = [
    # Player(name="Wilfredo Leon",      team="Perugia",   role="outside",  price=30),
    # Player(name="Yoandy Leal",        team="Trento",    role="outside",  price=28),
    # Player(name="Earvin Ngapeth",     team="Modena",    role="outside",  price=27),
    # Player(name="Osmany Juantorena",  team="Civitanova",role="outside",  price=25),
    # Player(name="Simone Giannelli",   team="Trento",    role="setter",   price=26),
    # Player(name="Dragan Travica",     team="Modena",    role="setter",   price=20),
    # Player(name="Fabio Balaso",       team="Civitanova",role="libero",   price=22),
    # Player(name="Jenia Grebennikov",  team="Modena",    role="libero",   price=21),
    # Player(name="Ivan Zaytsev",       team="Modena",    role="opposite", price=29),
    # Player(name="Tine Urnaut",        team="Civitanova",role="opposite", price=24),
    # Player(name="Robertlandy Simon",  team="Perugia",   role="middle",   price=23),
    # Player(name="Srecko Lisinac",     team="Trento",    role="middle",   price=22),
]

db.add_all(players)
db.commit()
db.close()
print(f"Seeded {len(players)} players.")