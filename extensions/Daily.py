import json
import requests
import sys
import datetime as dt
from datetime import datetime, timedelta
from pymongo import MongoClient
import threading
import hikari
import lightbulb
import typing
import time

headers = {}

bot = None

async def getCurrentGuilds():
    if bot is not None:
        currentGuilds = []
        async for item in bot.rest.fetch_my_guilds():
            currentGuilds.append(str(item.id))
        print(currentGuilds)
        updateGuilds(currentGuilds)
    else:
        print("botD = none")
    
def removeGuild(guild_id):
    client = MongoClient("")
    print("Connection Successful")
    db = client['ClashBot']
    clan_collection = db['Clan']
    member_collection = db['Member']
    
    clan_collection.update_one(
            {'guilds':str(guild_id)}, 
            {'$set':{"dateTime" : str(dt.date.today())}}
        )
    clan_collection.update_many(
            {'guilds':str(guild_id)}, 
            {'$pull':{'guilds':str(guild_id)}}
        )
    print(f'Guild removed {guild_id}')

def updateGuilds(currentGuilds):
    client = MongoClient("")
    print("Connection Successful")
    db = client['ClashBot']
    clan_collection = db['Clan']
    member_collection = db['Member']

    
    for clan in clan_collection.find():
        
        if len(clan['guilds']) > 0:

            for guild in clan['guilds']:
                
                if str(guild) not in currentGuilds:
                    print(f'impostor {clan["name"]}')
                    removeGuild(str(guild))
                else:
                    print(f'crewmate {clan["name"]}')
        else:
            print(f'no guilds {clan["name"]}')

def removeClan(clan_tag):
    client = MongoClient("")
    print("Connection Successful")
    db = client['ClashBot']
    clan_collection = db['Clan']
    member_collection = db['Member']

    print(f"removing clan: {clan_tag}")

    clan_collection.delete_one({"tag": clan_tag})
    member_collection.delete_many({"clan_tag": clan_tag})

def findInactiveClans():
    client = MongoClient("")
    print("Connection Successful")
    db = client['ClashBot']
    clan_collection = db['Clan']
    member_collection = db['Member']
    # Checks for clans older than inactiveTimer and removes them
    inactiveTimer = 30
    for clan in clan_collection.find():
        if(dt.date.today() - timedelta(inactiveTimer) >= datetime.strptime(clan["dateTime"],"%Y-%m-%d").date()):
            removeClan(clan["tag"])

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def getClanApi(clan_tag):
    clan_tag = clan_tag.strip()
    clan_tag = clan_tag.lower()
    if (clan_tag[0] == '#'):
        clan_tag = clan_tag[1:]
    api_url = f'https://api.clashofclans.com/v1/clans/%23{clan_tag}'
    response = requests.get(api_url,headers=headers)
    print(f'clan response code {response.status_code}')
    return response.json()

def daily():
    client = MongoClient("")
    print("Connection Successful")
    db = client['ClashBot']
    clan_collection = db['Clan']
    member_collection = db['Member']

    clan_list = []
    for clan in clan_collection.find():
        clan_list.append(f'{clan["tag"]}')
        if len(clan["guilds"]) != 0:
            clan_collection.update_one(
                {"tag": clan["tag"]}, 
                {'$set':
                    {"dateTime" : str(dt.date.today())}
                }
            )
    uprint(clan_list)
    getCurrentGuilds()
    findInactiveClans()
    for clan_tag in clan_list:
        clan = getClanApi(clan_tag)
        uprint(clan['name'])
        clan_dict = {
            "tag":clan["tag"],
            "name": clan["name"],
            "clanLevel": clan["clanLevel"]
            }
        # if clan_collection.find_one({"tag" : clan["tag"]}) is None:
        #     clan_collection.insert_one(clan_dict)
        # else:
        #     clan_collection.replace_one({"tag" : clan["tag"]}, clan_dict)


        for member in clan["memberList"]:
            member_tag = member["tag"]
            player_api_url = f'https://api.clashofclans.com/v1/players/%23{member_tag[1:]}'
            
            player_response = requests.get(player_api_url,headers=headers)
            player = player_response.json()
            
            member_dict = {
                "dateTime" : str(dt.date.today()),
                "tag" : member["tag"],
                "name" : member["name"],
                "clan_tag": clan["tag"],
                "clan_name": clan["name"],
                "role" : member["role"],
                "trophies" : member["trophies"],
                "clanrank" : member["clanRank"],
                "achievements":{}
            }
            for achievement in player["achievements"]:
                if(achievement["name"] == "Get those other Goblins!"):
                    member_dict["achievements"]["Get those Goblins!"] = achievement["value"]
                else:   
                    member_dict["achievements"][achievement["name"]] = achievement["value"]

            if member_collection.find_one({"tag" : member["tag"],"dateTime" : member_dict["dateTime"]}) is None:
                member_collection.insert_one(member_dict)
            else:
                member_collection.replace_one({"tag" : member["tag"],"dateTime" : member_dict["dateTime"]}, member_dict)
                #uprint(member_dict["name"])
        # print(str(clan_dict))

    client.close()
def checkTime():
    # This function runs periodically every 1 second
    threading.Timer(1, checkTime).start()

    now = datetime.utcnow()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    if(current_time == '20:00:00'):  # check if matches with the desired time
        daily()
print(datetime.utcnow())
