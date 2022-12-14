import hikari
import lightbulb
from datetime import datetime
import threading
import extensions.Daily as Daily
import json

cFile = open('config.json',)
config = json.load(cFile)
discordToken = config['discordToken']

bot = lightbulb.BotApp(token=discordToken,)

@bot.listen(hikari.StartedEvent)
async def bot_startup(event):
    Daily.bot = bot
    await Daily.getCurrentGuilds()
    print("bot has started")
    
@bot.listen(hikari.GuildMessageCreateEvent)
async def print_messages(event):
    print(f"hikari.GuildMessageCreateEvent event.content = {event.content}")

bot.load_extensions('extensions.Leaderboard','extensions.Clan')

bot.run()

