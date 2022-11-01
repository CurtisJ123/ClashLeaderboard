import json
import requests
import sys
from pymongo import MongoClient
import datetime
import lightbulb
import hikari


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

# region getResourceAchievement()
def getResourceAchievement(Resource):
    if (Resource == "gold"):
        leaderboardResource = 'Gold Grab'
    elif (Resource == "elixir"):
        leaderboardResource = 'Elixir Escapade'
    elif (Resource == "dark elixir"):
        leaderboardResource = 'Heroic Heist'
    elif (Resource == "dark"):
        leaderboardResource = 'Heroic Heist'
    elif (Resource == "g"):
        leaderboardResource = 'Gold Grab'
    elif (Resource == "e"):
        leaderboardResource = 'Elixir Escapade'
    elif (Resource == "d"):
        leaderboardResource = 'Heroic Heist'
    elif (Resource == "donations"):
        leaderboardResource = 'Donations'
    else:
        return "resource not found"
    return leaderboardResource
# endregion

# region getClan()
def getClan(guild_id):
    try:
        clan_tag = clan_collection.find_one({'guilds': f"{guild_id}"})["tag"]
        clan_tag = clan_tag[1:]
        return clan_tag
    except TypeError as e:
        print("An exception occured ::",e)
        return False
    except:
        print("Something went wrong")
        return False
# endregion

# region getTimeFrame()
def getTimeFrame(timeFrame):
    day = datetime.timedelta(1)
    week = datetime.timedelta(7)
    month = datetime.timedelta(30)
    if (timeFrame == "day"):
        leaderboardTimeFrame = day
    elif (timeFrame == "week"):
        leaderboardTimeFrame = week
    elif (timeFrame == "month"):
        leaderboardTimeFrame = month
    else:
        return "timeframe not found"
    return leaderboardTimeFrame
# endregion

# region getLeaderBoard()
def getLeaderBoard(timeFrame, Resource, clan_tag, playerCount):
    #region timeFrame and resource delcaration
    timeFrame = timeFrame.lower()
    Resource = Resource.lower()

    leaderboardResource = getResourceAchievement(Resource)
    print(leaderboardResource)

    if(leaderboardResource == "resource not found"):
        print("resource not found")
        return (hikari.Embed(title=f'resource not found',description="",color='E5D6D3'))
    #endregion

    playerCount = int(playerCount)
    #region Headers
    headers = {}
    #endregion
    
    leaderboard_dict = {}

    # get latest member_collection 
    
    member_cursor = member_collection.find({"clan_tag": f"#{clan_tag}", "dateTime": str(datetime.date.today())})
    
    # if no data for current day use previous
    if len(list(member_cursor.clone())) == 0:
        member_cursor = member_collection.find({"clan_tag": f"#{clan_tag}", "dateTime": str(datetime.date.today()-datetime.timedelta(1))})
    
    for member in member_cursor:
        leaderboardTimeFrame = getTimeFrame(timeFrame)
        member_tag = member["tag"]
        player = member
        dbmember = None
        while dbmember is None:
            dbmember = member_collection.find_one(
            {"tag": member_tag, "dateTime": str(datetime.date.today() - leaderboardTimeFrame)})
            if leaderboardTimeFrame > datetime.timedelta(1):
                leaderboardTimeFrame -= datetime.timedelta(1)
            else:
                break
        if (dbmember is None):
            continue

        achievement_dict = dbmember["achievements"]
        player_achievement_dict = {}
        player_dict = player["achievements"]
        
        for item in player_dict:
            if(item == "Get those other Goblins!"):
                player_achievement_dict["Get those Goblins!"] = player_dict[item]
            else:
                player_achievement_dict[item] = player_dict[item]
        leaderboard_dict[member_tag] = {
            "name": member["name"],
            "tag": member["tag"]
        }
        for achievement, value in achievement_dict.items():
            leaderboard_dict[member_tag][achievement] = player_achievement_dict[achievement] - value
        leaderboard_dict[member_tag]["Donations"] = leaderboard_dict[member_tag]["Friend in Need"] + leaderboard_dict[member_tag]["Sharing is caring"] + (leaderboard_dict[member_tag]["Siege Sharer"] * 30)
        if(member_tag.lower() == "#uvqpcglg"):
            print(leaderboard_dict[member_tag]["Donations"])
            print(leaderboard_dict[member_tag]["Friend in Need"])
            print(leaderboard_dict[member_tag]["Sharing is caring"])
            print(leaderboard_dict[member_tag]["Siege Sharer"])
    #leaderboard = []

    res = sorted(leaderboard_dict, key=lambda x: (
        leaderboard_dict[x][leaderboardResource]), reverse=True)
    if len(res) == 0:
        return (hikari.Embed(title=f'res = 0',description="",color='FFCCCC'))

    response = requests.get(f'https://api.clashofclans.com/v1/clans/%23{clan_tag}', headers=headers)
    clan = response.json()
    print(f'clan response code {response.status_code}')
    embed = (
        hikari.Embed(
            title=f'{leaderboardResource}',
            description="{timeF} {days}".format(timeF=getTimeFrame(timeFrame).days,days = "Days" if getTimeFrame(timeFrame).days > 1 else "Day"),
            color='E5D6D3'
            )
        .set_thumbnail(f"{clan['badgeUrls']['large']}")
        .set_footer(f"{clan['tag']}")
    )
    for i, user in enumerate(res):
            if i < playerCount:
                if(leaderboardResource == "Donations"):
                    total = leaderboard_dict[user]["Friend in Need"] + leaderboard_dict[user]["Sharing is caring"] + (leaderboard_dict[user]["Siege Sharer"] * 30)
                    total = f'{total:,d}'
                else:
                    total = f'{leaderboard_dict[user][leaderboardResource]:,d}'
                embed.add_field(f'{i+1}, {leaderboard_dict[user]["name"]} : ', f'{total}')
    print("getLeaderboard() Complete")
    return embed
# endregion


plugin = lightbulb.Plugin('Leaderboard')

# region getleaderboard command
@plugin.command()
@lightbulb.option("resource", "Gold, Elixir, Dark Elixir, or Donations!", hikari.OptionType.STRING,required=True)
@lightbulb.option("time", "Day, Week, or Month!", hikari.OptionType.STRING)
@lightbulb.option("players","How many players you want to display on the leaderboard",default=10)
@lightbulb.command('getleaderboard', 'GetLeaderBoard!')
@lightbulb.implements(lightbulb.SlashCommand)
async def LeaderBoard(ctx: lightbulb.SlashContext) -> None:
    rp = await ctx.respond("Please Wait ...")
    #msg = await rp.message()
    clan_tag = getClan(ctx.guild_id)
    if clan_tag is not False:
        LeaderboardEmbed = getLeaderBoard(ctx.options.time,ctx.options.resource,clan_tag,ctx.options.players)
        await ctx.edit_last_response(content="",embed=LeaderboardEmbed)
    else:
        await ctx.edit_last_response("No clan found, Please set a clan with /setclan")

# endregion


def load(bot):
    bot.add_plugin(plugin)

