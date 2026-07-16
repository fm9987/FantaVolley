import sqlite3
conn = sqlite3.connect('fantasy.db')
conn.execute("UPDATE rosters SET gameweek=1")
conn.commit()
conn.close()


## What commands to execute

# The one sets every single row in rosters to have gameweek set to 1
# conn.execute("UPDATE rosters SET gameweek=1")
