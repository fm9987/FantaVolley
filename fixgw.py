import sqlite3
conn = sqlite3.connect('fantasy.db')
conn.execute("UPDATE rosters SET gameweek=1")
conn.commit()
conn.close()