import json
import requests
import sys
import datetime as dt
from datetime import datetime
import lightbulb
import hikari
import time

from pymongo import MongoClient


client = MongoClient("")
print("Connection Successful")
db = client['ClashBot']
clan_collection = db['Clan']
member_collection = db['Member']

# region uprint()
def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding

    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        def f(obj): return str(obj).encode(
            enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)
# endregion

# region getClanTag()
def getClanTag(guild_id):
    try:
        clan_tag = clan_collection.find_one({'guilds': f"{guild_id}"})["tag"]
        clan_tag = clan_tag[1:]
        return clan_tag
    except TypeError as e:
        print("An exception occured ::",e)
        return False
    except Exception as e:
        print("Something went wrong ::",e)
        return False
# endregion

# region clanInfo()
async def clanInfo(guild_id):
    guild_id = int(guild_id)
    clan_tag = getClanTag(guild_id)
    api_url = f'https://api.clashofclans.com/v1/clans/%23{clan_tag}'
    #region Headers
    headers = {}
    #endregion
    response = requests.get(api_url, headers=headers)
    clan = response.json()
    embed = (
        hikari.Embed(title=f'{clan["name"]}', description=f'{clan["description"]}',color='E5D6D3')
        .add_field("Level", f'{clan["clanLevel"]}')
        .add_field("Members", f'{clan["members"]}\n Should be new line')
        .set_thumbnail(f"{clan['badgeUrls']['large']}")
        .set_footer(f"{clan['tag']}")
    )
    return embed
# endregion

def removeGuild(guild_id):
    
    #clan_collection.update_one({"tag": f'{guild_id}'},{'$pull':{'guilds':f'{guild_id}'}})
    clan_collection.update_one(
            {'guilds':str(guild_id)}, 
            {'$set':{"dateTime" : str(dt.date.today())}}
        )
    clan_collection.update_many(
            {'guilds':str(guild_id)}, 
            {'$pull':{'guilds':str(guild_id)}}
        )
    print(f'Guild removed {guild_id}')
# region setClan()
def setClan(clan_tag, guild_id):
    client = MongoClient(
        "mongodb+srv://test-user:test-password@atlascluster.facatz3.mongodb.net/?retryWrites=true&w=majority")
    print("Connection Successful")
    db = client['ClashBot']
    clan_collection = db['Clan']
    member_collection = db['Member']
    guild_id = int(guild_id)
    clan_tag = clan_tag.strip()
    clan_tag = clan_tag.lower()
    if (clan_tag[0] == '#'):
        clan_tag = clan_tag[1:]
    api_url = f'https://api.clashofclans.com/v1/clans/%23{clan_tag}'
    headers = {}
    response = requests.get(api_url, headers=headers)
    print(f'clan response code {response.status_code}')
    clan = response.json()
    clan_dict = {
        "dateTime" : str(dt.date.today()),
        "tag": clan["tag"],
        "name": clan["name"],
        "clanLevel": clan["clanLevel"],
        "guilds":[]
    }
    if clan_collection.find_one({"guilds": f'{guild_id}'}) is None:
        print("No clan found")
    else:
        print("Found Clan")
        removeGuild(guild_id)
    
    if clan_collection.find_one({"tag": clan["tag"]}) is None:
        clan_collection.insert_one(clan_dict)
        clan_collection.update_one(
            {"tag": clan["tag"]}, 
            {'$push':{
                'guilds':f'{guild_id}'
                }
            }
        )
    else:
        #clan_collection.replace_one({"tag": clan["tag"]}, clan_dict)
        clan_collection.update_one(
            {"tag": clan["tag"]}, 
            {'$push':{
                'guilds':f'{guild_id}'
                }
            }
        )
    print(f"Server clan set to {clan_dict['name']}")
    return clan_dict["name"]
# endregion

plugin = lightbulb.Plugin('Clan')

# region setclan command
@plugin.command()
@lightbulb.option("clantag", "Input the clan tag")
@lightbulb.command('setclan', 'Set which clan belongs to this discord server')
@lightbulb.implements(lightbulb.SlashCommand)
async def setclan(ctx: lightbulb.SlashContext) -> None:
    rp = await ctx.respond("Please Wait ...")
    msg = await rp.message()
    await ctx.edit_last_response(f"Server clan set to {setClan(ctx.options.clantag,ctx.guild_id)}")
    # await msg.add_reaction("🏆")
# endregion

# region claninfo command
@plugin.command()
@lightbulb.command('claninfo', 'Displays clan info')
@lightbulb.implements(lightbulb.SlashCommand)
async def setclan(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond("Please Wait ...")
    embed = await clanInfo(ctx.guild_id)
    await ctx.edit_last_response(content="",embed=embed)
    
# endregion




def load(bot):
    bot.add_plugin(plugin)
