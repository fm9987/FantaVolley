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

Milano = [
    Player(name="Porro Simone",           team="Milano", role="setter"),
    Player(name="Orduna Santiago",        team="Milano", role="setter"),
    Player(name="Dermaux Basil",          team="Milano", role="opposite"),
    Player(name="Argano Federico",        team="Milano", role="opposite"),
    Player(name="Recine Francesco",       team="Milano", role="outside"),
    Player(name="Ichino Tommaso",         team="Milano", role="outside"),
    Player(name="Rotty Seppe",            team="Milano", role="outside"),
    Player(name="Otsuka Tatsunori",       team="Milano", role="outside"),
    Player(name="Tatarov Georgi",         team="Milano", role="outside"),
    Player(name="Benacchio Alessandro",   team="Milano", role="middle"),
    Player(name="Tenorio Davi",           team="Milano", role="middle"),
    Player(name="Bartolucci Filippo",     team="Milano", role="middle"),
    Player(name="Simon Aties Robertlandy",team="Milano", role="middle"),
    Player(name="Catania Damiano",        team="Milano", role="libero"),
    Player(name="Corbetta Jacopo",        team="Milano", role="libero"),
]

Cuneo = [
    Player(name="Argilagos Bryan",        team="Cuneo", role="setter"),
    Player(name="Coscione Manuel",        team="Cuneo", role="setter"),
    Player(name="Sala Lorenzo",           team="Cuneo", role="opposite"),
    Player(name="Feral Nathan",           team="Cuneo", role="opposite"),
    Player(name="Khanzadeh Poriya Hossein",team="Cuneo", role="outside"),
    Player(name="Strehlau Alexandre",     team="Cuneo", role="outside"),
    Player(name="Champlin Ethan",         team="Cuneo", role="outside"),
    Player(name="Giraudo Federico",       team="Cuneo", role="outside"),
    Player(name="Codarin Lorenzo",        team="Cuneo", role="middle"),
    Player(name="Barberio Emanuele",      team="Cuneo", role="middle"),
    Player(name="Mosca Leandro",          team="Cuneo", role="middle"),
    Player(name="Volpe Nicolo",           team="Cuneo", role="middle"),
    Player(name="Cavaccini Domenico",     team="Cuneo", role="libero"),
    Player(name="Loubeyre Thibault",      team="Cuneo", role="libero"),
]

Trentino = [
    Player(name="Zonta Nicola",           team="Trentino", role="setter"),
    Player(name="Sbertoli Riccardo",      team="Trentino", role="setter"),
    Player(name="Jansons Renars-Pauls",   team="Trentino", role="opposite"),
    Player(name="Faure Theo",             team="Trentino", role="opposite"),
    Player(name="Roberti Federico",       team="Trentino", role="outside"),
    Player(name="Michieletto Alessandro", team="Trentino", role="outside"),
    Player(name="Lavia Daniele",          team="Trentino", role="outside"),
    Player(name="Xavier Adriano",         team="Trentino", role="outside"),
    Player(name="Torwie Simon",           team="Trentino", role="middle"),
    Player(name="Bossi Elia",             team="Trentino", role="middle"),
    Player(name="Gualberto Flavio",       team="Trentino", role="middle"),
    Player(name="Nedeljkovic Aleksandar", team="Trentino", role="middle"),
    Player(name="Laurenzano Gabriele",    team="Trentino", role="libero"),
    Player(name="Gollini Riccardo",       team="Trentino", role="libero"),
]

Monza = [
    Player(name="Rowan Andrew",           team="Monza", role="setter"),
    Player(name="Bonacchi Leonardo",      team="Monza", role="setter"),
    Player(name="Frascio Diego",          team="Monza", role="opposite"),
    Player(name="Mapelli Nicolo",         team="Monza", role="opposite"),
    Player(name="Velichkov Zhasmin",      team="Monza", role="outside"),
    Player(name="Khotsevych Hryhorii",    team="Monza", role="outside"),
    Player(name="Massari Jacopo",         team="Monza", role="outside"),
    Player(name="Perin Pierre",           team="Monza", role="outside"),
    Player(name="Beretta Thomas",         team="Monza", role="middle"),
    Player(name="Fall Bara",              team="Monza", role="middle"),
    Player(name="Petkov Iliya",           team="Monza", role="middle"),
    Player(name="Ceban Victorio",         team="Monza", role="middle"),
    Player(name="Pesaresi Nicola",        team="Monza", role="libero"),
    Player(name="Morazzini Flavio",       team="Monza", role="libero"),
]

Civitanova = [
    Player(name="Nikolov Simeon",         team="Civitanova", role="setter"),
    Player(name="Zoppellari Francesco",   team="Civitanova", role="setter"),
    Player(name="Tonkonoh Maksym",        team="Civitanova", role="opposite"),
    Player(name="Loeppky Eric",           team="Civitanova", role="outside"),
    Player(name="Nikolov Aleksandar",     team="Civitanova", role="outside"),
    Player(name="Bottolo Mattia",         team="Civitanova", role="outside"),
    Player(name="Duflos-Rossi Noa",       team="Civitanova", role="outside"),
    Player(name="Gardini Davide",         team="Civitanova", role="outside"),
    Player(name="Polo Alberto",           team="Civitanova", role="middle"),
    Player(name="Klimes Antonin",         team="Civitanova", role="middle"),
    Player(name="Gargiulo Giovanni Maria",team="Civitanova", role="middle"),
    Player(name="Howe Jackson",           team="Civitanova", role="middle"),
    Player(name="Bisotto Francesco",      team="Civitanova", role="libero"),
    Player(name="Balaso Fabio",           team="Civitanova", role="libero"),
]

Padova = [
    Player(name="Behnezhad Arshia",       team="Padova", role="setter"),
    Player(name="Rinaldi Simone",         team="Padova", role="setter"),
    Player(name="Golzadeh Amir Mohammad", team="Padova", role="opposite"),
    Player(name="Mills Brendan",          team="Padova", role="opposite"),
    Player(name="Bristot Alessandro",     team="Padova", role="outside"),
    Player(name="Bergamasco Francesco",   team="Padova", role="outside"),
    Player(name="Leodolter Leonardo Lukas",team="Padova", role="outside"),
    Player(name="Orioli Mattia",          team="Padova", role="outside"),
    Player(name="Ruzza Andrea",           team="Padova", role="middle"),
    Player(name="Truocchio Andrea",       team="Padova", role="middle"),
    Player(name="Kunstmann Joscha",       team="Padova", role="middle"),
    Player(name="Pellacani Marco",        team="Padova", role="middle"),
    Player(name="D Amico Francesco",      team="Padova", role="libero"),
    Player(name="Uliana Mattia",          team="Padova", role="libero"),
]

Perugia = [
    Player(name="Giannelli Simone",       team="Perugia", role="setter"),
    Player(name="Cappadona Stefano",      team="Perugia", role="setter"),
    Player(name="Reggers Ferre",          team="Perugia", role="opposite"),
    Player(name="Kollator David",         team="Perugia", role="opposite"),
    Player(name="Henno Mathis",           team="Perugia", role="outside"),
    Player(name="Semeniuk Kamil",         team="Perugia", role="outside"),
    Player(name="Plotnytskyi Oleh",       team="Perugia", role="outside"),
    Player(name="Hosseini Seyed Matin",   team="Perugia", role="outside"),
    Player(name="Loser Agustin",          team="Perugia", role="middle"),
    Player(name="Sole Sebastian",         team="Perugia", role="middle"),
    Player(name="Sanguinetti Giovanni",   team="Perugia", role="middle"),
    Player(name="Crosato Federico",       team="Perugia", role="middle"),
    Player(name="Loreti Luca",            team="Perugia", role="libero"),
    Player(name="Gaggini Marco",          team="Perugia", role="libero"),
]

Prata = [
    Player(name="Alberini Alessio",       team="Prata", role="setter"),
    Player(name="Marsili Sebastiano",     team="Prata", role="setter"),
    Player(name="Klets Kirill",           team="Prata", role="opposite"),
    Player(name="Pol Alberto",            team="Prata", role="outside"),
    Player(name="Terpin Jernej",          team="Prata", role="outside"),
    Player(name="Bergmann Lukas",         team="Prata", role="outside"),
    Player(name="Bayram Efe",             team="Prata", role="outside"),
    Player(name="D Heer Wout",            team="Prata", role="middle"),
    Player(name="Katalan Nicolo",         team="Prata", role="middle"),
    Player(name="Larizza Jacopo",         team="Prata", role="middle"),
    Player(name="Toscani Alessandro",     team="Prata", role="libero"),
    Player(name="Guadagnini Federico",    team="Prata", role="libero"),
]

Modena = [
    Player(name="Tizi-Oualou Amir",       team="Modena", role="setter"),
    Player(name="Barbanti Leonardo",      team="Modena", role="setter"),
    Player(name="Mujanovic Nik",          team="Modena", role="opposite"),
    Player(name="Meijs Sil",              team="Modena", role="opposite"),
    Player(name="Porro Luca",             team="Modena", role="outside"),
    Player(name="Garello Nicolo",         team="Modena", role="outside"),
    Player(name="Jaeschke Thomas",        team="Modena", role="outside"),
    Player(name="Pardo Mati",             team="Modena", role="middle"),
    Player(name="Tauletta Luca",          team="Modena", role="middle"),
    Player(name="Di Martino Gabriele",    team="Modena", role="middle"),
    Player(name="Russo Roberto",          team="Modena", role="middle"),
    Player(name="Perry Luke",             team="Modena", role="libero"),
    Player(name="Menchetti Federico",     team="Modena", role="libero"),
]

Cisterna = [
    Player(name="Fanizza Alessandro",     team="Cisterna", role="setter"),
    Player(name="Szabo Vilmos",           team="Cisterna", role="setter"),
    Player(name="Martinez Miguel Angel",  team="Cisterna", role="opposite"),
    Player(name="Barotto Tommaso",        team="Cisterna", role="opposite"),
    Player(name="Lanza Filippo",          team="Cisterna", role="outside"),
    Player(name="Magalini Giulio",        team="Cisterna", role="outside"),
    Player(name="Magliano Lorenzo",       team="Cisterna", role="outside"),
    Player(name="Mazzone Daniele",        team="Cisterna", role="middle"),
    Player(name="Tosti Jacopo",           team="Cisterna", role="middle"),
    Player(name="Peng Shikun",            team="Cisterna", role="middle"),
    Player(name="Federici Filippo",       team="Cisterna", role="libero"),
    Player(name="Pierri Francesco",       team="Cisterna", role="libero"),
]


# db.add_all(Cisterna)
db.commit()
db.close()
print(f"Seeded all the players.")