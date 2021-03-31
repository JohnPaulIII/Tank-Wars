import os
import asyncio
import discord
from discord.ext import commands
import time
import sys
from Framework import GameCommands as TankGame

dir_path = os.path.dirname(os.path.realpath(__file__))

client = discord.Client()
bot = commands.Bot(command_prefix="!GM ")

TOKEN = 'ODA2MjE5MjIxODg0NjAwMzMw.YBmQKQ.Tq5Iw5Hfua1O6PKGF5_FNhU7b1o'

def checkAdmin(ctx):
    for role in ctx.author.roles:
        if role.name == "Admin" or role.name == "Developers" or role.name == "Tank Beta Tester":
            return True
    return checkOwner(ctx)

def checkOwner(ctx):
    if ctx.author.id in [571867069214097423, 385044173289553920]:
        return True
    return False

@bot.command()
async def quickstart(ctx):
    if checkAdmin(ctx):
        global quickstarts
        if ctx.channel.id in quickstarts:
            settings = quickstarts[ctx.channel.id]
            if settings[0] == "tanks":
                await start(ctx, settings[0],  settings[1], settings[2], settings[3], settings[4], settings[5])

@bot.command()
async def status(ctx):
    if checkOwner(ctx):
        asyncio.ensure_future(runChecks(ctx))

async def runChecks(ctx):
    global tankgames
    await ctx.channel.purge()
    for game in tankgames.values():
        gamenum, channel, stage = game.getStatus()
        await ctx.send("A game is being run on {}, currently on game {}, stage {}.".format(channel.name, str(int(gamenum)), str(int(stage))))

@bot.command()
async def downtime(ctx):
    if checkAdmin(ctx):
        await ctx.channel.purge()
        await ctx.send("This bot is currently undergoing maintenance, we will be back up shortly")
        global tankgametasks
        for game in tankgametasks.values():
            game.cancel()
        quit()

@bot.command()
async def start(ctx, *settings):
    if checkAdmin(ctx):
        gamelist = [
            "tanks"
        ]
        await ctx.channel.purge()
        grabbot = await ctx.send('Starting up...', delete_after = 5)
        newchannel = grabbot.channel
        if len(settings) == 0 or not settings[0] in gamelist:
            await failedstart(ctx)
        else:
            if settings[0] == gamelist[0]: #tanks - video channel, number of commands
                tankstart(ctx, newchannel, settings[1:])

@bot.command()
async def endgame(ctx):
    if checkAdmin(ctx):
        global tankgametasks
        global tankgames
        gamecount = 0
        targetchannel = None
        for channel, game in tankgametasks.items():
            if channel == ctx.channel.id:
                game.cancel()
                gamecount += 1
                targetchannel = channel
        if not targetchannel == None:
            del tankgametasks[targetchannel]
            del tankgames[targetchannel]
        await ctx.channel.purge()
        await ctx.send('Ended {} games'.format(str(int(gamecount))), delete_after = 10)


async def failedstart(ctx):
    await ctx.send('Starting call failed', delete_after = 5)

def tankstart(ctx, channel, settings):
    global tankgametasks
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    gameobject = loop.create_task(tankgameloop(fut, ctx, channel, settings))
    #gameobject = asyncio.ensure_future(tankgameloop(ctx, channel, settings))
    tankgametasks[channel.id] = gameobject


async def tankgameloop(fut, ctx, channel, settings):
    try:
        global tankgames
        minPlayers = int(settings[2])
        maxWaittime = int(settings[3])
        gameWaittime = int(settings[4])
        pingback = await channel.send('Tank game started in channel {} with {} settings'.format(channel, len(settings)), delete_after = 5)
        channels = await pingback.guild.fetch_channels()
        for c in channels:
            if c.id == int(settings[0]):
                videochannel = c
        gameobject = TankGame([pingback.author], pingback.channel, videochannel, settings[1])
        tankgames[channel.id] = gameobject
        while True:
            await gameobject.newGame()
            waittime = maxWaittime
            while waittime > 0:
                await asyncio.sleep(5)
                count = await gameobject.checkPlayerCount()
                if count < minPlayers:
                    waittime = maxWaittime
                    if 'waitmessage' in locals():
                        await waitmessage.edit(content = 'Waiting for players ({}/{})...'.format(count, minPlayers))
                    else:
                        waitmessage = await channel.send('Waiting for players ({}/{})...'.format(count, minPlayers))
                else:
                    waittime -= 5
                    if 'waitmessage' in locals():
                        await waitmessage.edit(content = 'Game will start in {} seconds'.format(waittime))
                    else:
                        waitmessage = await channel.send('Game will start in {} seconds'.format(waittime))
            await waitmessage.edit(content = 'Let The Games Begin!', delete_after = 5)
            del waitmessage
            await gameobject.gamesetup()
            looper = False
            while not looper:
                waittime = gameWaittime
                while waittime > 0:
                    await asyncio.sleep(5)
                    waittime -= 5
                    if 'waitmessage' in locals():
                        await waitmessage.edit(content = 'Round will end in {} seconds'.format(waittime))
                    else:
                        waitmessage = await channel.send('Round will end in {} seconds'.format(waittime))
                await waitmessage.edit(content = 'Calculating...')
                looper = await gameobject.executeRound()
                await waitmessage.delete()
                del waitmessage
            await asyncio.sleep(15)
            await gameobject.endgameCleanup()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException) as error:
        gameobject.adderrorlog(error.text)
        gameobject.adderrorlog(str(error.status))
        gameobject.adderrorlog(str(error.code))
    except:
        gameobject.adderrorlog("Error2")
    finally:
        gameobject.adderrorlog("Error2")
        fut.set_result("Error1")


@bot.command()
async def test(ctx):
    if checkAdmin(ctx):
        print(checkAdmin(ctx))

@bot.command()
async def clear(ctx):
    if checkAdmin(ctx):
        await ctx.channel.purge()
        await ctx.channel.send('Ready!')

@bot.command()
async def channel(ctx):
    if checkAdmin(ctx):
        global MAINCHANNEL
        global botuser
        await ctx.send(ctx.message.channel.id)
        MAINCHANNEL = bot.get_channel(ctx.message.channel.id)
        print(MAINCHANNEL)
        await ctx.send(MAINCHANNEL)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.event
async def on_ready():
    global MAINCHANNEL
    global botuser
    global tankgames
    global tankgametasks
    global quickstarts
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Tank Wars"))
    MAINCHANNEL = bot.get_channel(820511266715992064)
    grabbot = await MAINCHANNEL.send('Ready!')
    botuser = grabbot.author
    tankgames = {}
    tankgametasks = {}
    quickstarts = {
        806287252279394325:["tanks", "813859705209225257", "2", "2", "15", "30"], 
        816067342894759947:["tanks", "816067343058075718", "2", "2", "15", "30"], 
        819591197970530314:["tanks", "819591235295641650", "2", "3", "15", "30"]
        }

@bot.event
async def on_reaction_add(reaction, user):
    global tankgames
    global botuser
    if not user == botuser:
        result = checkReactions(reaction, user)
        if result[0] == 2:
            await reaction.remove(user)
        elif result[0] == 1:
            if result[1] == "tanks":
                await result[2].checkReaction(reaction, user)

def checkReactions(reaction, user):
    global tankgames
    channelid = reaction.message.channel.id
    messageid = reaction.message.id
    for channel, gameobject in tankgames.items():
        if channel == channelid:
            result = gameobject.getCommandMessages()
            for message in result[0]:
                if message.id == messageid:
                    if reaction.emoji in result[1]:
                        return (1, "tanks", gameobject)
                    else:
                        return (2, None, None)
    return (0, None, None)

bot.run(TOKEN)


