# main.py
import os
import logging
from dotenv import load_dotenv

import discord
from discord.ext import commands

# Load env variables (BOT token, DB URL, etc.)
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("holi_bot")

# Create a bot instance with necessary intents
intents = discord.Intents.default()
intents.members = True  # required to manage roles and get Member info
bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Bot is online! Logged in as {bot.user} (ID: {bot.user.id})")

def load_cogs():
    """Statically load specific cogs."""
    try:
        bot.load_extension("cogs.holi")  # The Holi commands
        logger.info("Loaded cog: cogs.holi")
    except Exception as e:
        logger.error(f"Failed to load cog 'cogs.holi': {e}")

if __name__ == "__main__":
    load_cogs()
    bot.run("TOKEN")
