# seed_players.py
from db import init_db, SessionLocal, Player

init_db()
db = SessionLocal()


# Teams
Verona = [
    Player(name="Zingel Aidan",           team="Verona", role="middle"),
    Player(name="Cortesia Lorenzo",       team="Verona", role="middle"),
    Player(name="Valbusa Marco",          team="Verona", role="middle"),
    Player(name="Gironi Fabrizio",        team="Verona", role="opposite"),
    Player(name="Planinsic Uros",         team="Verona", role="setter"),
    Player(name="D'Amico Francesco",      team="Verona", role="libero"),
    Player(name="Staforini Matteo",       team="Verona", role="libero"),
    Player(name="Keita Noumory",          team="Verona", role="outside"),
    Player(name="Sani Francesco",         team="Verona", role="outside"),
    Player(name="Christenson Micah",      team="Verona", role="setter"),
    Player(name="Bonisoli Pietro",        team="Verona", role="libero"),
    Player(name="Glatz Lukas",            team="Verona", role="outside"),
    Player(name="Vitelli Marco",          team="Verona", role="middle"),
    Player(name="Ferreira Souza Darlan",  team="Verona", role="opposite"),
    Player(name="Mozic Rok",              team="Verona", role="outside"),
    Player(name="Nedeljkovic Aleksandar", team="Verona", role="middle"),
]

Piacenza = [
    Player(name="Porro Paolo",            team="Piacenza", role="setter"),
    Player(name="Leon Henri Emmanuel",    team="Piacenza", role="opposite"),
    Player(name="Pace Domenico",          team="Piacenza", role="libero"),
    Player(name="Mandiraci Ramazan Efe",  team="Piacenza", role="outside"),
    Player(name="Comparoni Francesco",    team="Piacenza", role="middle"),
    Player(name="Galassi Gianluca",       team="Piacenza", role="middle"),
    Player(name="Simon Robertlandy",      team="Piacenza", role="middle"),
    Player(name="Travica Dragan",         team="Piacenza", role="setter"),
    Player(name="Andringa Robbert",       team="Piacenza", role="outside"),
    Player(name="Bergmann Lukas Felipe",  team="Piacenza", role="outside"),
    Player(name="Iyegbekedo Daniel",      team="Piacenza", role="middle"),
    Player(name="Gutierrez Jose Miguel",  team="Piacenza", role="outside"),
    Player(name="Bovolenta Alessandro",   team="Piacenza", role="opposite"),
    Player(name="Loreti Luca",            team="Piacenza", role="libero"),
    Player(name="Seddik Joris",           team="Piacenza", role="middle"),
]

db.add_all(Verona)
db.add_all(Piacenza)
db.commit()
db.close()
print(f"Seeded all the players.")