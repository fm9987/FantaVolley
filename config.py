import os
from dotenv import load_dotenv

load_dotenv()  # reads .env and loads into os.environ

TOKEN      = os.getenv("DISCORD_TOKEN")
GUILD_ID   = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

# Fantasy league settings
MAX_ROSTER_SIZE = 12
LINEUP_SIZE     = 6   # starters per week
TRADE_TIMEOUT   = 48  # hours to accept/decline