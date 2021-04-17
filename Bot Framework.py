import os
import asyncio
import discord
from discord.ext import commands
import time
import sys
import pandas as pd
import numpy as np
import datetime
from NewFramework import GameCommands as TankGame

dir_path = os.path.dirname(os.path.realpath(__file__))

client = discord.Client()
if sys.platform.startswith('linux'):
    bot = commands.Bot(command_prefix="!GM ")
else:
    bot = commands.Bot(command_prefix="!DM ")

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

def make_ordinal(n):
    n = int(n)
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix

@bot.command(aliases = ['qs'])
@commands.check(checkAdmin)
async def quickstart(ctx):
    global quickstarts
    if ctx.channel.id in quickstarts:
        settings = quickstarts[ctx.channel.id]
        if settings[0] == "tanks":
            await start(ctx, settings[0],  settings[1], settings[2], settings[3], settings[4], settings[5])

@bot.command()
@commands.check(checkOwner)
async def status(ctx):
    asyncio.ensure_future(runChecks(ctx))

async def runChecks(ctx):
    global tankgames
    await ctx.channel.purge()
    for game in tankgames.values():
        gamenum, channel, stage = game.getStatus()
        await ctx.send("A game is being run on {}, currently on game {}, stage {}.".format(channel.name, str(int(gamenum)), str(int(stage))))

@bot.command()
@commands.check(checkAdmin)
async def downtime(ctx):
    await ctx.channel.purge()
    await ctx.send("This bot is currently undergoing maintenance, we will be back up shortly")
    global tankgametasks
    for game in tankgametasks.values():
        game.cancel()
    quit()

@bot.command()
@commands.check(checkAdmin)
async def start(ctx, *settings):
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

@bot.command(aliases = ['eg'])
@commands.check(checkAdmin)
async def endgame(ctx):
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
            await gameobject.gamesetup2()
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
                looper = await gameobject.executeRound2()
                await waitmessage.delete()
                del waitmessage
            await asyncio.sleep(15)
            await gameobject.endgameCleanup()
    except (discord.NotFound, discord.Forbidden, discord.HTTPException) as error:
        gameobject.adderrorlog(error.text)
        gameobject.adderrorlog(str(error.status))
        gameobject.adderrorlog(str(error.code))
    except Exception as error:
        gameobject.adderrorlog(error)
    finally:
        gameobject.adderrorlog("Error2")
        fut.set_result("Error1")


@bot.command()
@commands.check(checkAdmin)
async def test(ctx):
    print(checkAdmin(ctx))

@bot.command()
@commands.check(checkAdmin)
async def clear(ctx):
    await ctx.channel.purge()
    await ctx.channel.send('Ready!')

@bot.command()
@commands.check(checkAdmin)
async def channel(ctx):
    global MAINCHANNEL
    global botuser
    await ctx.send(ctx.message.channel.id)
    MAINCHANNEL = bot.get_channel(ctx.message.channel.id)
    print(MAINCHANNEL)
    await ctx.send(MAINCHANNEL)

@bot.command()
@commands.check(checkAdmin)
async def server(ctx):
    await ctx.send(ctx.guild.id)
    print(ctx.guild.id)

@bot.command()
async def stats(ctx, *args):
    if len(args) == 0:
        caller = ctx.author
    elif len(args) == 1:
        if args[0][:3] == '<@!' and args[0][-1:] == '>':
            caller = await ctx.guild.fetch_member(int(args[0][3:-1]))
        else:
            await ctx.send('Could not identify {}, please use their @name'.format(args[0]))
    else:
        await ctx.send('Too many arguments received.')
        return
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Servers', str(int(ctx.guild.id)), 'pandaFiles', '{}#{}.csv'.format(caller.name, caller.discriminator))
    newembed = discord.Embed(
        title = 'Personal Stats', 
        description = 'These are {}\'s personal stats'.format(caller.mention),
        color = 7419530,
        timestamp = datetime.datetime.utcnow()
    )
    newembed.set_footer(
        text = 'Brought to you by Game Master', 
        icon_url = 'https://cdn.discordapp.com/avatars/806219221884600330/a1805614d671284f7e0dc0578cfa13e4.png'
    )
    newembed.set_thumbnail(url = 'https://cdn.discordapp.com/avatars/806219221884600330/a1805614d671284f7e0dc0578cfa13e4.png')
    newembed.set_author(
        name = caller.display_name, 
        icon_url = caller.avatar_url
    )
    if os.path.isfile(filepath):
        df = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Servers', str(int(ctx.guild.id)), 'pandaFiles', 'MasterTankList.csv'), sep=';', index_col='Tanks')
        callerfullname = '{}#{}'.format(caller.name, caller.discriminator)
        newdf = df.sort_values(by = 'Last Game')
        df1 = newdf.sort_values(by = 'Kills', ascending=False).reset_index()
        df2 = newdf.sort_values(by = 'Wins', ascending=False).reset_index()
        print(df1)
        newembed.add_field(
            name = 'Stats', inline = False,
            value = '```Kills     {}\nDeaths    {}\nWins      {}\nLosses    {}```'.format(
                df.loc[callerfullname, 'Kills'],
                df.loc[callerfullname, 'Deaths'],
                df.loc[callerfullname, 'Wins'],
                df.loc[callerfullname, 'Losses']
            )
        )
        '''
        newembed.add_field(
            name = 'Value', inline = True,
            value = '{}\n{}\n{}\n{}'.format(
                df.loc[callerfullname, 'Kills'],
                df.loc[callerfullname, 'Deaths'],
                df.loc[callerfullname, 'Wins'],
                df.loc[callerfullname, 'Losses']
            )
        )
        '''
        newembed.add_field(
            name = 'Kill Ranking:', inline = False,
            value = '{} is currently ranked {} in overall kills'.format(caller.mention, make_ordinal(np.flatnonzero(df1['Tanks'] == callerfullname)[0] + 1))
        )
        newembed.add_field(
            name = 'Win Ranking:', inline = False,
            value = '{} is currently ranked {} in overall wins'.format(caller.mention, make_ordinal(np.flatnonzero(df2['Tanks'] == callerfullname)[0] + 1))
        )
    else:
        newembed.add_field(
            name = 'Unknown Status',
            value = '{} currently has no recorded stats available, probably due to never having played Tank Wars on this server.'.format(caller.display_name)
            )
    await ctx.send(embed = newembed)

@bot.command(aliases = ['rivals', 'rivalry'])
async def rival(ctx, *args):
    if len(args) == 1:
        if args[0][:3] == '<@!' and args[0][-1:] == '>':
            first_name = '{}#{}'.format(ctx.author.name, ctx.author.discriminator)
            first_callsign = ctx.author.mention
            user = await ctx.guild.fetch_member(int(args[0][3:-1]))
            second_name = '{}#{}'.format(user.name, user.discriminator)
            second_callsign = user.mention
        else:
            await ctx.send('The name given could not be identified, please use their @name')
            return
    elif len(args) == 2:
        if args[0][:3] == '<@!' and args[0][-1:] == '>' and args[1][:3] == '<@!' and args[1][-1:] == '>':
            user = await ctx.guild.fetch_member(int(args[0][3:-1]))
            first_name = '{}#{}'.format(user.name, user.discriminator)
            first_callsign = user.mention
            user = await ctx.guild.fetch_member(int(args[1][3:-1]))
            second_name = '{}#{}'.format(user.name, user.discriminator)
            second_callsign = user.mention
        else:
            await ctx.send('One or both of these given names could not be identified, please use their @name(s)')
            return
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Servers', str(int(ctx.guild.id)), 'pandaFiles', '{}.csv'.format(first_name))
    if os.path.isfile(filepath):
        df = pd.read_csv(filepath, sep=';', index_col = 'Tanks')
        print(df)
        if second_name in df.index:
            newembed = discord.Embed(
                title = 'Rivalry', 
                description = '{} wants to know about the rivalry between {} and {}'.format(ctx.author.mention, first_callsign, second_callsign),
                color = 7419530,
                timestamp = datetime.datetime.utcnow()
            )
            newembed.set_footer(
                text = 'Brought to you by Game Master', 
                icon_url = 'https://cdn.discordapp.com/avatars/806219221884600330/a1805614d671284f7e0dc0578cfa13e4.png'
            )
            newembed.set_author(
                name = ctx.author.display_name, 
                icon_url = ctx.author.avatar_url
            )
            newembed.add_field(
                name = 'Results', inline = False,
                value = '{} has killed {} {} times\n{} has killed {} {} times'.format(first_callsign, second_callsign, df.loc[second_name, 'Kills'], second_callsign, first_callsign, df.loc[second_name, 'Killed'])
            )
            await ctx.send(embed = newembed)
            print(df.loc[second_name])
        else:
            await ctx.send('{} has not played against {} in Tank Wars on this server.'.format(first_callsign, second_callsign))
    else:
        await ctx.send('{} has not played Tank Wars on this server.'.format(first_callsign))

@bot.command()
@commands.check(checkOwner)
async def embed(ctx):
    caller = ctx.author
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Servers', str(int(ctx.guild.id)), 'pandaFiles', '{}#{}.csv'.format(caller.name, caller.discriminator))
    newembed = discord.Embed(
        title = 'Personal Stats', 
        description = 'These are {}\'s personal stats'.format(caller.mention),
        color = 7419530,
        timestamp = datetime.datetime.utcnow()
    )
    newembed.set_footer(
        text = 'Brought to you by Game Master', 
        icon_url = 'https://cdn.discordapp.com/avatars/806219221884600330/a1805614d671284f7e0dc0578cfa13e4.png'
    )
    newembed.set_thumbnail(url = 'https://cdn.discordapp.com/avatars/806219221884600330/a1805614d671284f7e0dc0578cfa13e4.png')
    newembed.set_author(
        name = caller.display_name, 
        icon_url = caller.avatar_url
    )
    if os.path.isfile(filepath):
        df = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Servers', str(int(ctx.guild.id)), 'pandaFiles', 'MasterTankList.csv'), sep=';', index_col='Tanks')
        callerfullname = '{}#{}'.format(caller.name, caller.discriminator)
        newdf = df.sort_values(by = 'Last Game')
        df1 = newdf.sort_values(by = 'Kills', ascending=False).reset_index()
        df2 = newdf.sort_values(by = 'Wins', ascending=False).reset_index()
        print(df1)
        newembed.add_field(
            name = 'Stats', inline = False,
            value = '```Kills     {}\nDeaths    {}\nWins      {}\nLosses    {}```'.format(
                df.loc[callerfullname, 'Kills'],
                df.loc[callerfullname, 'Deaths'],
                df.loc[callerfullname, 'Wins'],
                df.loc[callerfullname, 'Losses']
            )
        )
        '''
        newembed.add_field(
            name = 'Value', inline = True,
            value = '{}\n{}\n{}\n{}'.format(
                df.loc[callerfullname, 'Kills'],
                df.loc[callerfullname, 'Deaths'],
                df.loc[callerfullname, 'Wins'],
                df.loc[callerfullname, 'Losses']
            )
        )
        '''
        newembed.add_field(
            name = 'Kill Ranking:', inline = False,
            value = '{} is currently ranked {} in overall kills'.format(caller.display_name, make_ordinal(np.flatnonzero(df1['Tanks'] == callerfullname)[0] + 1))
        )
        newembed.add_field(
            name = 'Win Ranking:', inline = False,
            value = '{} is currently ranked {} in overall wins'.format(caller.display_name, make_ordinal(np.flatnonzero(df2['Tanks'] == callerfullname)[0] + 1))
        )
    else:
        newembed.add_field(
            name = 'Unknown Status',
            value = '{} currently has no recorded stats available, probably due to never having played Tank Wars on this server.'.format(caller.display_name)
            )
    await ctx.send(embed = newembed)


@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')
    print(ctx.author.name + '#' + ctx.author.discriminator)
    print(type(ctx.author.mention))

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
        806287252279394325:["tanks", "813859705209225257", "2", "2", "5", "30"], 
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

@bot.event
async def on_message(ctx):
    await bot.process_commands(ctx)
    #print("Message Recieved")

bot.run(TOKEN)


